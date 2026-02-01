import cv2
import numpy as np
import time

# =======================
# SCORER
# =======================

class SimpleScorer:
    def __init__(self):
        self.obstacle_hits = 0
        self.track_segments_completed = []
        self.start_time = None
        self.box_score = 0

    def start_run(self):
        self.start_time = time.time()
        self.obstacle_hits = 0
        self.track_segments_completed = []
        self.box_score = 0

    def get_obstacle_score(self):
        return max(0, 5 - self.obstacle_hits)

    def get_total_score(self):
        return self.box_score + self.get_obstacle_score()


# =======================
# BLUE DROP ZONE
# =======================

def detect_blue_drop_zone(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Dark blue on white
    lower_blue = np.array([95, 50, 20])
    upper_blue = np.array([135, 255, 255])

    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Thicken thin outlines
    kernel = np.ones((7, 7), np.uint8)
    blue_mask = cv2.dilate(blue_mask, kernel, iterations=1)
    blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(
        blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    if hierarchy is None:
        return None, None, blue_mask

    outer = None
    inner = None

    for i, cnt in enumerate(contours):
        if cv2.contourArea(cnt) < 500:
            continue

        if hierarchy[0][i][3] == -1:
            if outer is None or cv2.contourArea(cnt) > cv2.contourArea(outer):
                outer = cnt
        else:
            if inner is None or cv2.contourArea(cnt) > cv2.contourArea(inner):
                inner = cnt

    return inner, outer, blue_mask


# =======================
# RED TRACK + OBSTACLES
# =======================

def detect_red_track_and_obstacles(frame, exclude_blue_mask):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red track
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    red_mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower_red1, upper_red1),
        cv2.inRange(hsv, lower_red2, upper_red2)
    )

    # Fill gaps only
    red_mask = cv2.morphologyEx(
        red_mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1
    )

    track_contours, _ = cv2.findContours(
        red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    track_contours = [c for c in track_contours if cv2.contourArea(c) > 500]

    # Track area for obstacle filtering
    track_area = cv2.dilate(red_mask, np.ones((40, 40), np.uint8), iterations=1)

    # Dark obstacles
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, dark_mask = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)

    # Remove red shadows
    red_shadow = cv2.bitwise_or(
        cv2.inRange(hsv, (0, 30, 20), (10, 150, 60)),
        cv2.inRange(hsv, (160, 30, 20), (180, 150, 60))
    )

    obstacle_mask = cv2.bitwise_and(dark_mask, cv2.bitwise_not(red_shadow))
    obstacle_mask = cv2.bitwise_and(obstacle_mask, track_area)
    obstacle_mask = cv2.bitwise_and(obstacle_mask, cv2.bitwise_not(red_mask))
    obstacle_mask = cv2.bitwise_and(obstacle_mask, cv2.bitwise_not(exclude_blue_mask))

    obstacle_mask = cv2.morphologyEx(
        obstacle_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=1
    )
    obstacle_mask = cv2.morphologyEx(
        obstacle_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1
    )

    obstacle_contours, _ = cv2.findContours(
        obstacle_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    obstacle_contours = [c for c in obstacle_contours if cv2.contourArea(c) > 150]

    return red_mask, track_contours, obstacle_mask, obstacle_contours


# =======================
# ROBOT
# =======================

def detect_robot(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower = np.array([40, 100, 100])
    upper = np.array([80, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), 1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    c = max(contours, key=cv2.contourArea)
    if cv2.contourArea(c) < 300:
        return None

    M = cv2.moments(c)
    if M["m00"] == 0:
        return None

    return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))


# =======================
# HELPERS
# =======================

def check_robot_on_obstacle(robot_pos, obstacles):
    if robot_pos is None:
        return False
    return any(abs(cv2.pointPolygonTest(c, robot_pos, True)) < 20 for c in obstacles)


def check_if_non_white_in_inner_zone(frame, inner):
    if inner is None:
        return 0

    mask = np.zeros(frame.shape[:2], np.uint8)
    cv2.drawContours(mask, [inner], -1, 255, -1)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ratio = np.sum((gray > 10) & (gray < 240) & (mask == 255)) / np.sum(mask == 255)

    return 5 if ratio > 0.8 else 4 if ratio > 0.6 else 2 if ratio > 0.3 else 1 if ratio > 0.1 else 0


# =======================
# MAIN
# =======================

def main(video_source=0, debug=True):
    cap = cv2.VideoCapture(video_source)
    scorer = SimpleScorer()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        inner, outer, blue_mask = detect_blue_drop_zone(frame)
        red_mask, tracks, obstacle_mask, obstacles = detect_red_track_and_obstacles(frame, blue_mask)
        robot = detect_robot(frame)

        vis = frame.copy()

        for c in tracks:
            cv2.drawContours(vis, [c], -1, (0, 255, 0), 3)

        if outer is not None:
            cv2.drawContours(vis, [outer], -1, (255, 0, 0), 3)
        if inner is not None:
            cv2.drawContours(vis, [inner], -1, (255, 150, 0), 3)

        cv2.drawContours(vis, obstacles, -1, (0, 0, 255), 3)

        if robot:
            cv2.circle(vis, robot, 12, (0, 255, 255), -1)

        cv2.imshow("Scorer", vis)
        if debug:
            cv2.imshow("Blue Mask", blue_mask)
            cv2.imshow("Red Mask", red_mask)
            cv2.imshow("Obstacle Mask", obstacle_mask)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main(video_source=0, debug=True)
