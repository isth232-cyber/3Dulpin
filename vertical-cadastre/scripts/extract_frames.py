import cv2
import glob
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input directory containing mp4s")
    parser.add_argument("--output", required=True, help="Output directory for extracted images")
    parser.add_argument("--max-frames", type=int, default=300, help="Target total frames to extract")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    videos = glob.glob(os.path.join(args.input, "*.mp4"))
    
    if not videos:
        print("No videos found.")
        return

    # Calculate total duration
    total_frames = 0
    video_details = []
    for f in videos:
        v = cv2.VideoCapture(f)
        fc = int(v.get(cv2.CAP_PROP_FRAME_COUNT))
        if fc > 0:
            total_frames += fc
            video_details.append((f, fc))
        v.release()

    print(f"Total source frames across {len(video_details)} videos: {total_frames}")
    
    if total_frames == 0:
        return

    # Determine step size to get max_frames
    step = max(1, total_frames // args.max_frames)
    print(f"Extracting 1 frame every {step} frames to target {args.max_frames} total frames.")

    extracted_count = 0
    current_global_frame = 0

    for f, fc in video_details:
        print(f"Processing {os.path.basename(f)} ({fc} frames)...")
        v = cv2.VideoCapture(f)
        
        for i in range(fc):
            ret, frame = v.read()
            if not ret:
                break
                
            if current_global_frame % step == 0:
                # Save frame
                out_path = os.path.join(args.output, f"frame_{extracted_count:05d}.jpg")
                cv2.imwrite(out_path, frame)
                extracted_count += 1
                
                if extracted_count >= args.max_frames:
                    v.release()
                    print(f"Reached target {args.max_frames}. Stopping.")
                    return
                    
            current_global_frame += 1
            
        v.release()

    print(f"Done. Extracted {extracted_count} frames to {args.output}")

if __name__ == "__main__":
    main()
