import cv2
import numpy as np
import time
from collections import deque

class SimpleObstacleCourseTracker:
    """
    Real-time obstacle course tracker with:
    - Homography bird's-eye view
    - Robot position dot
    - Live score counter
    """
    
    def __init__(self):
        self.homography_matrix = None
        self.track_corners = None
        self.mapped_size = (800, 1200)  # Width x Height for vertical track
        
        # Scoring state
        self.score = 0
        self.start_time = None
        self.obstacle_penalty_count = 0
        self.last_contact_time = 0
        self.contact_cooldown = 1.0  # Seconds between penalty counts
        
        # Robot tracking
        self.robot_trail = deque(maxlen=50)  # Show trail of robot movement
        
        # Detected features
        self.obstacles = []
        self.red_path_mask = None
        
    def select_track_corners(self, image):
        """
        Click 4 corners of the track board: top-left, top-right, bottom-right, bottom-left
        """
        corners = []
        display_img = image.copy()
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(corners) < 4:
                corners.append([x, y])
                color = (0, 255, 0)
                cv2.circle(display_img, (x, y), 8, color, -1)
                labels = ["1:TL", "2:TR", "3:BR", "4:BL"]
                cv2.putText(display_img, labels[len(corners)-1], 
                           (x+15, y-10), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.8, color, 2)
                cv2.imshow("Select Track Corners", display_img)
        
        cv2.imshow("Select Track Corners", display_img)
        cv2.setMouseCallback("Select Track Corners", mouse_callback)
        
        print("\n" + "="*60)
        print("CALIBRATION: Click 4 corners of the WHITE BOARD")
        print("Order: 1) Top-Left  2) Top-Right  3) Bottom-Right  4) Bottom-Left")
        print("Press SPACE when done")
        print("="*60)
        
        while len(corners) < 4:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC to cancel
                cv2.destroyAllWindows()
                return None
        
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        
        self.track_corners = np.array(corners, dtype=np.float32)
        print("✓ Corners selected successfully!")
        return self.track_corners
    
    def compute_homography(self):
        """Compute transformation matrix for bird's-eye view"""
        if self.track_corners is None:
            raise ValueError("Must select corners first!")
        
        dst_corners = np.array([
            [0, 0],
            [self.mapped_size[0], 0],
            [self.mapped_size[0], self.mapped_size[1]],
            [0, self.mapped_size[1]]
        ], dtype=np.float32)
        
        self.homography_matrix, _ = cv2.findHomography(
            self.track_corners, dst_corners
        )
        print("✓ Homography computed!")
        return self.homography_matrix
    
    def warp_to_birds_eye(self, image):
        """Transform to bird's-eye view"""
        if self.homography_matrix is None:
            return image
        
        warped = cv2.warpPerspective(
            image, self.homography_matrix, self.mapped_size
        )
        return warped
    
    def detect_obstacles(self, warped_image):
        """
        Detect cardboard box obstacles (brown/tan boxes on the track)
        """
        hsv = cv2.cvtColor(warped_image, cv2.COLOR_BGR2HSV)
        
        # Detect brown/cardboard boxes
        lower_brown1 = np.array([5, 30, 60])
        upper_brown1 = np.array([25, 180, 200])
        
        lower_brown2 = np.array([10, 20, 40])
        upper_brown2 = np.array([30, 150, 150])
        
        mask1 = cv2.inRange(hsv, lower_brown1, upper_brown1)
        mask2 = cv2.inRange(hsv, lower_brown2, upper_brown2)
        brown_mask = cv2.bitwise_or(mask1, mask2)
        
        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        brown_mask = cv2.morphologyEx(brown_mask, cv2.MORPH_CLOSE, kernel)
        brown_mask = cv2.morphologyEx(brown_mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(
            brown_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        self.obstacles = []
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area > 3000:  # Minimum size for obstacles
                x, y, w, h = cv2.boundingRect(cnt)
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    self.obstacles.append({
                        'id': i,
                        'contour': cnt,
                        'bbox': (x, y, w, h),
                        'center': (cx, cy),
                        'area': area
                    })
        
        return self.obstacles
    
    def detect_red_path(self, warped_image):
        """Detect the red path"""
        hsv = cv2.cvtColor(warped_image, cv2.COLOR_BGR2HSV)
        
        # Red color ranges (red wraps around in HSV)
        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        self.red_path_mask = cv2.bitwise_or(mask1, mask2)
        
        # Clean up
        kernel = np.ones((5, 5), np.uint8)
        self.red_path_mask = cv2.morphologyEx(
            self.red_path_mask, cv2.MORPH_CLOSE, kernel
        )
        
        return self.red_path_mask
    
    def detect_robot(self, warped_image):
        """
        Detect robot using color marker or motion.
        Default: detects green, yellow, or bright objects.
        Adjust colors based on your robot's marker!
        """
        hsv = cv2.cvtColor(warped_image, cv2.COLOR_BGR2HSV)
        
        # Try multiple color ranges
        # GREEN
        lower_green = np.array([40, 60, 60])
        upper_green = np.array([80, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        # YELLOW
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # BRIGHT (white/silver robot)
        lower_bright = np.array([0, 0, 180])
        upper_bright = np.array([180, 60, 255])
        mask_bright = cv2.inRange(hsv, lower_bright, upper_bright)
        
        # Combine masks
        mask = cv2.bitwise_or(mask_green, mask_yellow)
        mask = cv2.bitwise_or(mask, mask_bright)
        
        # Remove red path from mask (so we don't detect the path as robot)
        if self.red_path_mask is not None:
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(self.red_path_mask))
        
        # Find contours
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if contours:
            # Get largest contour
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            
            if area > 150:  # Minimum robot size
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy), largest, area
        
        return None, None, 0
    
    def check_obstacle_collision(self, robot_pos, robot_contour):
        """
        Check if robot is colliding with obstacles.
        Returns True if collision detected.
        """
        if robot_pos is None or not self.obstacles:
            return False
        
        current_time = time.time()
        
        for obs in self.obstacles:
            # Check distance between robot and obstacle
            obs_center = obs['center']
            distance = np.sqrt(
                (robot_pos[0] - obs_center[0])**2 + 
                (robot_pos[1] - obs_center[1])**2
            )
            
            # Collision threshold (adjust based on robot/obstacle size)
            collision_threshold = 80
            
            if distance < collision_threshold:
                # Apply cooldown to prevent multiple penalties for same collision
                if current_time - self.last_contact_time > self.contact_cooldown:
                    self.last_contact_time = current_time
                    return True
        
        return False
    
    def update_score(self, event_type):
        """Update score based on events"""
        if event_type == 'collision':
            self.obstacle_penalty_count += 1
            self.score -= 1
            print(f"⚠ COLLISION! Penalty applied. Score: {self.score}")
        elif event_type == 'start':
            self.start_time = time.time()
            print("▶ Run started!")
        elif event_type == 'finish':
            if self.start_time:
                elapsed = time.time() - self.start_time
                print(f"✓ Run finished in {elapsed:.2f} seconds!")
                if elapsed <= 60:
                    self.score += 5
                    print("⭐ Time bonus: +5 points!")
    
    def get_elapsed_time(self):
        """Get current elapsed time"""
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
    
    def draw_visualization(self, warped_image, robot_pos, robot_contour):
        """
        Create annotated bird's-eye view with:
        - Red path
        - Obstacles highlighted
        - Robot position dot
        - Score overlay
        """
        result = warped_image.copy()
        
        # Draw red path outline
        if self.red_path_mask is not None:
            # Find path contours
            path_contours, _ = cv2.findContours(
                self.red_path_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            cv2.drawContours(result, path_contours, -1, (0, 255, 255), 2)
        
        # Draw obstacles with labels
        for i, obs in enumerate(self.obstacles):
            cv2.drawContours(result, [obs['contour']], -1, (0, 165, 255), 3)
            x, y, w, h = obs['bbox']
            cv2.rectangle(result, (x, y), (x+w, y+h), (255, 0, 255), 2)
            
            # Label
            label_pos = (x + w//2 - 30, y - 10)
            cv2.putText(result, f"BOX {i+1}", label_pos,
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Draw robot position dot and trail
        if robot_pos:
            # Add to trail
            self.robot_trail.append(robot_pos)
            
            # Draw trail
            for i in range(1, len(self.robot_trail)):
                pt1 = self.robot_trail[i-1]
                pt2 = self.robot_trail[i]
                alpha = i / len(self.robot_trail)
                color = (0, int(255 * alpha), int(255 * (1-alpha)))
                cv2.line(result, pt1, pt2, color, 2)
            
            # Draw robot dot
            cv2.circle(result, robot_pos, 20, (0, 255, 0), -1)
            cv2.circle(result, robot_pos, 22, (255, 255, 255), 3)
            cv2.putText(result, "ROBOT", (robot_pos[0]-30, robot_pos[1]-30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw score overlay panel
        overlay = result.copy()
        panel_height = 120
        cv2.rectangle(overlay, (0, 0), (400, panel_height), (0, 0, 0), -1)
        result = cv2.addWeighted(overlay, 0.7, result, 0.3, 0)
        
        # Score text
        cv2.putText(result, f"SCORE: {self.score}", (10, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        
        # Time
        elapsed = self.get_elapsed_time()
        time_color = (0, 255, 0) if elapsed <= 60 else (0, 165, 255)
        cv2.putText(result, f"Time: {elapsed:.1f}s", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, time_color, 2)
        
        # Penalties
        cv2.putText(result, f"Penalties: {self.obstacle_penalty_count}", (10, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Instructions
        cv2.putText(result, "Q:Quit | R:Reset | S:Start", (420, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return result
    
    def reset_score(self):
        """Reset scoring state"""
        self.score = 0
        self.start_time = None
        self.obstacle_penalty_count = 0
        self.last_contact_time = 0
        self.robot_trail.clear()
        print("\n🔄 Score reset!")


def run_obstacle_course_tracker(video_source=2):
    """
    Main function to run the tracker
    video_source: 0 for webcam, or path to video file
    """
    print("\n" + "="*60)
    print("OBSTACLE COURSE TRACKER")
    print("="*60)
    
    # Initialize
    tracker = SimpleObstacleCourseTracker()
    cap = cv2.VideoCapture(video_source)
    
    if not cap.isOpened():
        print("❌ Error: Could not open video source")
        return
    
    # Read first frame for calibration
    ret, frame = cap.read()
    if not ret:
        print("❌ Error: Could not read frame")
        return
    
    # Calibration
    print("\nStep 1: Calibrating...")
    corners = tracker.select_track_corners(frame.copy())
    if corners is None:
        print("❌ Calibration cancelled")
        return
    
    tracker.compute_homography()
    print("\n✓ Calibration complete!")
    print("\nControls:")
    print("  S - Start run")
    print("  R - Reset score")
    print("  Q - Quit")
    print("="*60 + "\n")
    
    is_running = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Transform to bird's-eye view
        warped = tracker.warp_to_birds_eye(frame)
        
        # Detect features
        tracker.detect_red_path(warped)
        tracker.detect_obstacles(warped)
        
        # Detect robot
        robot_pos, robot_contour, robot_area = tracker.detect_robot(warped)
        
        # Check collisions
        if is_running and robot_pos:
            if tracker.check_obstacle_collision(robot_pos, robot_contour):
                tracker.update_score('collision')
        
        # Create visualization
        result = tracker.draw_visualization(warped, robot_pos, robot_contour)
        
        # Display
        cv2.imshow("Bird's-Eye View - Obstacle Course", result)
        cv2.imshow("Original Camera Feed", frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n👋 Quitting...")
            break
        elif key == ord('s'):
            tracker.update_score('start')
            is_running = True
        elif key == ord('r'):
            tracker.reset_score()
            is_running = False
        elif key == ord('f'):  # Manual finish
            if is_running:
                tracker.update_score('finish')
                is_running = False
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Final report
    print("\n" + "="*60)
    print("RUN COMPLETE")
    print("="*60)
    print(f"Final Score: {tracker.score}")
    print(f"Obstacle Penalties: {tracker.obstacle_penalty_count}")
    print(f"Time: {tracker.get_elapsed_time():.2f}s")
    print("="*60)


if __name__ == "__main__":
    # Run with webcam
    run_obstacle_course_tracker(video_source=2)
    
    # Or run with video file:
    # run_obstacle_course_tracker(video_source='obstacle_course.mp4')
