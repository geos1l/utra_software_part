import cv2
import numpy as np

# Global variables for trackbars
darkness_threshold = 60
blue_h_low = 100
blue_h_high = 130
blue_s_low = 80
blue_s_high = 255
blue_v_low = 50
blue_v_high = 150

def nothing(x):
    pass

def detect_red_track_and_obstacles_calibrated(frame, darkness_thresh, exclude_blue_mask):
    """
    Detect red track and obstacles with calibration
    Obstacles are DARK regions, but we exclude blue and handle shadows
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Detect red track
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)
    
    # Clean red mask
    kernel_small = np.ones((3, 3), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel_small, iterations=1)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel_small, iterations=2)
    
    # Get track contours
    track_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    track_contours = [cnt for cnt in track_contours if cv2.contourArea(cnt) > 500]
    
    # Simplify track contours
    clean_track = []
    for cnt in track_contours:
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        clean_track.append(approx)
    
    # Create track area
    kernel_dilate = np.ones((40, 40), np.uint8)
    track_area = cv2.dilate(red_mask, kernel_dilate, iterations=2)
    
    # Convert to grayscale AND HSV for shadow detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # SHADOW FILTERING SOLUTION:
    # Shadows on red track will still have red HUE but lower saturation/value
    # True black obstacles have NO specific hue
    
    # Get H, S, V channels
    h, s, v = cv2.split(hsv)
    
    # Find DARK regions
    _, dark_mask = cv2.threshold(gray, darkness_thresh, 255, cv2.THRESH_BINARY_INV)
    
    # Filter out shadows: dark regions that are ALSO red-ish
    # Shadows will have red hue (0-10 or 160-180)
    red_shadow_mask1 = cv2.inRange(hsv, np.array([0, 30, 20]), np.array([10, 150, darkness_thresh]))
    red_shadow_mask2 = cv2.inRange(hsv, np.array([160, 30, 20]), np.array([180, 150, darkness_thresh]))
    red_shadow_mask = cv2.bitwise_or(red_shadow_mask1, red_shadow_mask2)
    
    # Remove red shadows from dark mask
    dark_mask = cv2.bitwise_and(dark_mask, cv2.bitwise_not(red_shadow_mask))
    
    # Obstacles = dark regions IN track area, NOT red track, NOT blue zone
    obstacle_mask = cv2.bitwise_and(dark_mask, track_area)
    obstacle_mask = cv2.bitwise_and(obstacle_mask, cv2.bitwise_not(red_mask))
    obstacle_mask = cv2.bitwise_and(obstacle_mask, cv2.bitwise_not(exclude_blue_mask))
    
    # Clean up
    kernel_medium = np.ones((5, 5), np.uint8)
    obstacle_mask = cv2.morphologyEx(obstacle_mask, cv2.MORPH_OPEN, kernel_medium, iterations=2)
    obstacle_mask = cv2.morphologyEx(obstacle_mask, cv2.MORPH_CLOSE, kernel_medium, iterations=2)
    
    # Get obstacle contours
    obstacle_contours, _ = cv2.findContours(obstacle_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    obstacle_contours = [cnt for cnt in obstacle_contours if cv2.contourArea(cnt) > 150]
    
    # Simplify
    clean_obstacles = []
    for cnt in obstacle_contours:
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        clean_obstacles.append(approx)
    
    return red_mask, clean_track, obstacle_mask, clean_obstacles

def main_calibration(video_source=2):
    global darkness_threshold, blue_h_low, blue_h_high, blue_s_low, blue_s_high, blue_v_low, blue_v_high
    
    print("\n" + "="*60)
    print("OBSTACLE & BLUE ZONE CALIBRATION TOOL")
    print("="*60)
    print("Adjust sliders until:")
    print("  - Blue drop zone is detected correctly")
    print("  - Black obstacles are detected (white in obstacle mask)")
    print("  - Shadows on red track are NOT detected as obstacles")
    print("\nPress 'Q' to quit and see final values")
    print("Press 'S' to save current values")
    print("="*60 + "\n")
    
    cap = cv2.VideoCapture(video_source)
    
    if not cap.isOpened():
        print(f"❌ Can't open camera {video_source}")
        return
    
    # Create windows
    cv2.namedWindow('Calibration')
    
    # Darkness threshold
    cv2.createTrackbar('Darkness Thresh', 'Calibration', darkness_threshold, 255, nothing)
    
    # Blue detection sliders
    cv2.createTrackbar('Blue H Low', 'Calibration', blue_h_low, 179, nothing)
    cv2.createTrackbar('Blue H High', 'Calibration', blue_h_high, 179, nothing)
    cv2.createTrackbar('Blue S Low', 'Calibration', blue_s_low, 255, nothing)
    cv2.createTrackbar('Blue S High', 'Calibration', blue_s_high, 255, nothing)
    cv2.createTrackbar('Blue V Low', 'Calibration', blue_v_low, 255, nothing)
    cv2.createTrackbar('Blue V High', 'Calibration', blue_v_high, 255, nothing)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get trackbar values
        darkness_threshold = cv2.getTrackbarPos('Darkness Thresh', 'Calibration')
        blue_h_low = cv2.getTrackbarPos('Blue H Low', 'Calibration')
        blue_h_high = cv2.getTrackbarPos('Blue H High', 'Calibration')
        blue_s_low = cv2.getTrackbarPos('Blue S Low', 'Calibration')
        blue_s_high = cv2.getTrackbarPos('Blue S High', 'Calibration')
        blue_v_low = cv2.getTrackbarPos('Blue V Low', 'Calibration')
        blue_v_high = cv2.getTrackbarPos('Blue V High', 'Calibration')
        
        # Detect blue zone
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([blue_h_low, blue_s_low, blue_v_low])
        upper_blue = np.array([blue_h_high, blue_s_high, blue_v_high])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Clean blue mask
        kernel = np.ones((5, 5), np.uint8)
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Detect obstacles with calibrated values
        red_mask, track_contours, obstacle_mask, obstacle_contours = detect_red_track_and_obstacles_calibrated(
            frame, darkness_threshold, blue_mask
        )
        
        # Visualize
        result = frame.copy()
        
        # Draw red track
        cv2.drawContours(result, track_contours, -1, (0, 255, 0), 3)
        
        # Draw blue zone
        blue_contours, hierarchy = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if blue_contours:
            # Draw outer contour
            for i, cnt in enumerate(blue_contours):
                if cv2.contourArea(cnt) > 500:
                    if hierarchy[0][i][3] == -1:  # Outer
                        cv2.drawContours(result, [cnt], -1, (255, 0, 0), 3)
                    else:  # Inner
                        cv2.drawContours(result, [cnt], -1, (255, 150, 0), 3)
        
        # Draw obstacles
        cv2.drawContours(result, obstacle_contours, -1, (0, 0, 255), 3)
        
        # Add text
        cv2.putText(result, f"Darkness: {darkness_threshold}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(result, f"Blue H:{blue_h_low}-{blue_h_high} S:{blue_s_low}-{blue_s_high} V:{blue_v_low}-{blue_v_high}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(result, f"Obstacles detected: {len(obstacle_contours)}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Show windows
        cv2.imshow('Result', result)
        cv2.imshow('Red Track', red_mask)
        cv2.imshow('Blue Zone', blue_mask)
        cv2.imshow('Obstacles', obstacle_mask)
        
        # Keyboard
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n" + "="*60)
            print("CALIBRATED VALUES - Copy these into your main script:")
            print("="*60)
            print(f"\n# Darkness threshold (line ~40)")
            print(f"darkness_threshold = {darkness_threshold}")
            print(f"\n# Blue detection (in detect_blue_drop_zone function)")
            print(f"lower_blue = np.array([{blue_h_low}, {blue_s_low}, {blue_v_low}])")
            print(f"upper_blue = np.array([{blue_h_high}, {blue_s_high}, {blue_v_high}])")
            print("="*60 + "\n")
            break
        elif key == ord('s'):
            print("\n✅ CURRENT VALUES:")
            print(f"   Darkness threshold: {darkness_threshold}")
            print(f"   Blue: H:{blue_h_low}-{blue_h_high}, S:{blue_s_low}-{blue_s_high}, V:{blue_v_low}-{blue_v_high}\n")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main_calibration(video_source=0)