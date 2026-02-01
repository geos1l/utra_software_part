import cv2

def test_droidcam_sources():
    """Test camera sources with DirectShow for DroidCam"""
    print("Testing camera sources for DroidCam...")
    print("=" * 60)
    
    available_cameras = []
    
    # Test first 5 camera indices with and without DirectShow
    for i in range(5):
        print(f"\nTesting Camera {i}...")
        
        # Try with DirectShow (Windows)
        print(f"  Trying with DirectShow (CAP_DSHOW)...")
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"  ✓ Camera {i} with DirectShow: {width}x{height}")
                
                # Check if it's a black/placeholder frame
                mean_brightness = frame.mean()
                if mean_brightness > 10:  # Not completely black
                    print(f"  ✓ VALID FEED DETECTED (brightness: {mean_brightness:.1f})")
                    available_cameras.append((i, 'DirectShow'))
                    
                    # Show preview
                    cv2.imshow(f"Camera {i} - DirectShow", frame)
                    print(f"  Press any key to continue...")
                    cv2.waitKey(2000)
                    cv2.destroyAllWindows()
                else:
                    print(f"  ⚠ Black screen detected")
            cap.release()
        
        # Try without DirectShow
        print(f"  Trying without DirectShow...")
        cap = cv2.VideoCapture(i)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"  ✓ Camera {i} (default): {width}x{height}")
                
                mean_brightness = frame.mean()
                if mean_brightness > 10:
                    print(f"  ✓ VALID FEED DETECTED (brightness: {mean_brightness:.1f})")
                    available_cameras.append((i, 'default'))
                    
                    cv2.imshow(f"Camera {i} - Default", frame)
                    print(f"  Press any key to continue...")
                    cv2.waitKey(2000)
                    cv2.destroyAllWindows()
                else:
                    print(f"  ⚠ Black screen detected")
            cap.release()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    
    if available_cameras:
        print("\nAvailable cameras with valid feeds:")
        for idx, backend in available_cameras:
            print(f"  Camera {idx} ({backend})")
        
        print("\n" + "=" * 60)
        print("RECOMMENDED SETTINGS:")
        print("=" * 60)
        
        # Recommend the highest index (usually DroidCam)
        best_cam = available_cameras[-1]
        print(f"\nUse Camera Index: {best_cam[0]}")
        print(f"Backend: {best_cam[1]}")
        
        if best_cam[1] == 'DirectShow':
            print("\nIn your code, use:")
            print(f"  cap = cv2.VideoCapture({best_cam[0]}, cv2.CAP_DSHOW)")
        else:
            print("\nIn your code, use:")
            print(f"  cap = cv2.VideoCapture({best_cam[0]})")
        
    else:
        print("\n❌ No valid camera feeds found!")
        print("\nTroubleshooting:")
        print("  1. Make sure DroidCam app is running on your phone")
        print("  2. Make sure DroidCam client is connected on laptop")
        print("  3. Check if other apps can see DroidCam")
        print("  4. Try restarting DroidCam client")
    
    print("\n")

if __name__ == "__main__":
    test_droidcam_sources()