import cv2
import numpy as np


def find_white_rectangle(frame, brightness_threshold=180, min_area_pct=5, max_area_pct=60, erosion_size=5):
    """
    Find white stuff, erode to remove marble noise, filter by size, get the track board.
    
    Now returns the ACTUAL contour shape (not just bounding rectangle)
    
    Parameters you can adjust:
    - brightness_threshold: how bright to be "white" (0-255)
    - min_area_pct: minimum size as % of image (filters out small stuff)
    - max_area_pct: maximum size as % of image (filters out entire floor)
    - erosion_size: how much to erode (removes marble noise, keeps solid white track)
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Threshold: anything bright is white
    _, white_mask = cv2.threshold(gray, brightness_threshold, 255, cv2.THRESH_BINARY)
    
    # MORPHOLOGICAL EROSION - removes marble noise, keeps solid white areas
    kernel = np.ones((erosion_size, erosion_size), np.uint8)
    eroded_mask = cv2.erode(white_mask, kernel, iterations=2)
    
    # Optional: dilate back slightly to restore size (but keep sharp edges)
    dilated_mask = cv2.dilate(eroded_mask, kernel, iterations=1)
    
    # Calculate image area for filtering
    image_area = frame.shape[0] * frame.shape[1]
    min_area = image_area * (min_area_pct / 100)
    max_area = image_area * (max_area_pct / 100)
    
    # Find all white blobs
    contours, _ = cv2.findContours(dilated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, None, white_mask, eroded_mask, dilated_mask, []
    
    # Filter by size and find valid candidates
    valid_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area < area < max_area:
            valid_contours.append(cnt)
    
    if not valid_contours:
        return None, None, white_mask, eroded_mask, dilated_mask, contours
    
    # Get biggest valid contour (the track board)
    biggest = max(valid_contours, key=cv2.contourArea)
    
    # Instead of bounding rectangle, get the convex hull (follows the shape)
    hull = cv2.convexHull(biggest)
    
    # Simplify the hull to get main corner points (approximate as polygon)
    peri = cv2.arcLength(hull, True)
    approx_polygon = None

    for eps in np.linspace(0.005, 0.05, 25):
        approx = cv2.approxPolyDP(hull, eps * peri, True)
        if len(approx) == 4:
            approx_polygon = approx
            break

    if approx_polygon is None:
        approx_polygon = cv2.approxPolyDP(hull, 0.02 * peri, True)

    
    return biggest, approx_polygon, white_mask, eroded_mask, dilated_mask, contours


def mask_everything_outside_track(frame, track_contour):
    """
    Black out everything that's not inside the track contour.
    Now works with ANY polygon shape, not just rectangles.
    """
    # Create black mask
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    
    # Fill the track polygon with white
    cv2.fillPoly(mask, [track_contour.astype(np.int32)], 255)
    
    # Apply mask to frame
    result = cv2.bitwise_and(frame, frame, mask=mask)
    
    return result, mask


def main(video_source=0):
    print("\n" + "="*50)
    print("SIMPLE TRACK ISOLATOR WITH EROSION")
    print("="*50)
    print("Controls:")
    print("  Q - Quit")
    print("  + / - : Adjust brightness threshold")
    print("  ] / [ : Adjust MIN area %")
    print("  } / { : Adjust MAX area %")
    print("  > / < : Adjust EROSION size (KEY!)")
    print("="*50 + "\n")
    
    cap = cv2.VideoCapture(video_source)
    
    if not cap.isOpened():
        print(f"❌ Can't open camera {video_source}")
        print("Try changing video_source to 0, 1, or 2")
        return
    
    # Adjustable parameters
    brightness = 180
    min_area_pct = 5
    max_area_pct = 60
    erosion_size = 5  # KEY PARAMETER for removing marble noise
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Find the white track (now returns actual contour, not just rectangle)
        track_contour, track_polygon, white_mask, eroded_mask, dilated_mask, all_contours = find_white_rectangle(
            frame, brightness, min_area_pct, max_area_pct, erosion_size
        )
        
        # Create visualization
        frame_with_info = frame.copy()
        
        # Draw ALL contours in red (to see what's being detected)
        cv2.drawContours(frame_with_info, all_contours, -1, (0, 0, 255), 2)
        
        if track_contour is not None:
            # Draw the ACTUAL track shape in GREEN (follows the contour)
            cv2.drawContours(frame_with_info, [track_contour], -1, (0, 255, 0), 4)
            
            # Draw the simplified polygon in CYAN (corner points)
            cv2.polylines(frame_with_info, [track_polygon], True, (255, 255, 0), 3)
            
            # Draw corner points
            for i, point in enumerate(track_polygon):
                x, y = point[0]
                cv2.circle(frame_with_info, (x, y), 8, (255, 0, 255), -1)
                cv2.putText(frame_with_info, str(i+1), (x+10, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            
            # Mask everything outside
            masked_frame, mask = mask_everything_outside_track(frame, track_contour)
            
            # Show parameter info
            cv2.putText(frame_with_info, f"Brightness: {brightness} (+/-)", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame_with_info, f"Erosion: {erosion_size} (</>) <-- KEY", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame_with_info, f"Corners detected: {len(track_polygon)}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame_with_info, "GREEN = Track Contour", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame_with_info, "YELLOW = Simplified Polygon", (10, 145),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # Show results
            cv2.imshow("1. Track Detector", frame_with_info)
            cv2.imshow("2. Track Only (Isolated)", masked_frame)
            
            # Show morphology steps
            cv2.imshow("3a. Raw White Mask", white_mask)
            cv2.imshow("3b. After Erosion (Marble Removed)", eroded_mask)
            cv2.imshow("3c. After Dilation (Size Restored)", dilated_mask)
        else:
            # No valid track found
            cv2.putText(frame_with_info, "NO VALID TRACK", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(frame_with_info, "Increase EROSION (>) to remove marble", (50, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            
            # Still show params
            cv2.putText(frame_with_info, f"Brightness: {brightness} (+/-)", (10, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame_with_info, f"Erosion: {erosion_size} (</>) <-- KEY", (10, 160),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow("1. Track Detector", frame_with_info)
            
            # Show morphology steps even when no track detected
            cv2.imshow("3a. Raw White Mask", white_mask)
            cv2.imshow("3b. After Erosion (Marble Removed)", eroded_mask)
            cv2.imshow("3c. After Dilation (Size Restored)", dilated_mask)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        # Brightness adjustment
        elif key == ord('+') or key == ord('='):
            brightness = min(255, brightness + 5)
            print(f"Brightness: {brightness}")
        elif key == ord('-'):
            brightness = max(0, brightness - 5)
            print(f"Brightness: {brightness}")
        # Min area adjustment
        elif key == ord(']'):
            min_area_pct = min(100, min_area_pct + 1)
            print(f"Min area: {min_area_pct}%")
        elif key == ord('['):
            min_area_pct = max(0, min_area_pct - 1)
            print(f"Min area: {min_area_pct}%")
        # Max area adjustment
        elif key == ord('}'):
            max_area_pct = min(100, max_area_pct + 1)
            print(f"Max area: {max_area_pct}%")
        elif key == ord('{'):
            max_area_pct = max(0, max_area_pct - 1)
            print(f"Max area: {max_area_pct}%")
        # EROSION adjustment (KEY!)
        elif key == ord('>') or key == ord('.'):
            erosion_size = min(50, erosion_size + 1)
            print(f"Erosion size: {erosion_size} (removes more marble)")
        elif key == ord('<') or key == ord(','):
            erosion_size = max(1, erosion_size - 1)
            print(f"Erosion size: {erosion_size} (keeps more detail)")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\nFinal settings:")
    print(f"  Brightness: {brightness}")
    print(f"  Erosion: {erosion_size}")
    print(f"  Min area: {min_area_pct}%")
    print(f"  Max area: {max_area_pct}%")


if __name__ == "__main__":
    # Change to 0, 1, or 2 for your camera
    main(video_source=2)