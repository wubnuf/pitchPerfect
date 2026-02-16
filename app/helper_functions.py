import time
import os
import pyautogui
import numpy as np
import cv2
import pytesseract
import openai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Safety setting: set to False to allow pyautogui to move to screen edges
pyautogui.FAILSAFE = True
# Add a small pause between pyautogui actions for reliability
pyautogui.PAUSE = 0.3


def find_icon(
    screenshot_path,
    template_path,
    approx_x=None,
    approx_y=None,
    margin_x=100,
    margin_y=100,
    min_matches=10,
    threshold=0.8,
    scales=[0.9, 1.0, 1.1],
):
    img = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    if img is None:
        print("Error: Could not load screenshot.")
        return None, None

    if template is None:
        print("Error: Could not load template.")
        return None, None

    if approx_x is not None and approx_y is not None:
        H, W = img.shape[:2]
        x_start = max(0, approx_x - margin_x)
        y_start = max(0, approx_y - margin_y)
        x_end = min(W, approx_x + margin_x)
        y_end = min(H, approx_y + margin_y)
        cropped_img = img[y_start:y_end, x_start:x_end]
        offset_x, offset_y = x_start, y_start
    else:
        cropped_img = img
        offset_x, offset_y = 0, 0

    scene_gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(template_gray, None)
    kp2, des2 = orb.detectAndCompute(scene_gray, None)

    if des1 is not None and des2 is not None and len(des1) > 0 and len(des2) > 0:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda m: m.distance)

        if len(matches) > min_matches:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(
                -1, 1, 2
            )
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(
                -1, 1, 2
            )
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

            if M is not None:
                h_t, w_t = template_gray.shape
                pts = np.float32([[0, 0], [w_t, 0], [w_t, h_t], [0, h_t]]).reshape(
                    -1, 1, 2
                )
                dst_corners = cv2.perspectiveTransform(pts, M)

                center_x_cropped = int(np.mean(dst_corners[:, 0, 0]))
                center_y_cropped = int(np.mean(dst_corners[:, 0, 1]))
                center_x = center_x_cropped + offset_x
                center_y = center_y_cropped + offset_y
                return center_x, center_y

    # Fallback: Multi-Scale Template Matching
    img_gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)

    for scale in scales:
        resized_template = cv2.resize(
            template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
        )
        res = cv2.matchTemplate(img_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)

        if len(loc[0]) != 0:
            top_left = (loc[1][0], loc[0][0])
            tw, th = resized_template.shape[::-1]
            center_x_cropped = top_left[0] + tw // 2
            center_y_cropped = top_left[1] + th // 2
            center_x = center_x_cropped + offset_x
            center_y = center_y_cropped + offset_y
            return center_x, center_y

    return None, None


def connect_device():
    """
    For laptop mode, there is no physical device to connect.
    Returns a placeholder object. Screen interaction is done via pyautogui.
    """
    print("Running in laptop mode — no ADB device needed.")
    return "laptop"


def capture_screenshot(device, filename):
    """Capture the laptop screen using pyautogui."""
    os.makedirs("images", exist_ok=True)
    screenshot = pyautogui.screenshot()
    path = "images/" + str(filename) + ".png"
    screenshot.save(path)
    return path


def tap(device, x, y):
    """Click at (x, y) on the laptop screen."""
    pyautogui.click(x, y)


def input_text(device, text):
    """Type text using the laptop keyboard."""
    print("text to be written: ", text)
    pyautogui.typewrite(text, interval=0.03)


def swipe(device, x1, y1, x2, y2, duration=500):
    """Simulate a swipe/drag on the laptop screen."""
    duration_seconds = duration / 1000.0
    pyautogui.moveTo(x1, y1)
    pyautogui.mouseDown()
    pyautogui.moveTo(x2, y2, duration=duration_seconds)
    pyautogui.mouseUp()


def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text


def do_comparision(profile_image, sample_images):
    """
    Returns an average distance score for the best match among the sample_images.
    A lower score indicates a better match.
    """
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(profile_image, None)
    if des1 is None or len(des1) == 0:
        return float("inf")

    best_score = float("inf")
    for sample_image in sample_images:
        kp2, des2 = orb.detectAndCompute(sample_image, None)
        if des2 is None or len(des2) == 0:
            continue
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        if len(matches) == 0:
            continue

        matches = sorted(matches, key=lambda x: x.distance)
        score = sum([match.distance for match in matches]) / len(matches)
        if score < best_score:
            best_score = score

    return best_score if best_score != float("inf") else float("inf")


def generate_comment(profile_text):
    prompt = f"""
    Based on the following profile description, generate a 1-line friendly and personalized comment asking them to go out with you:

    Profile Description:
    {profile_text}

    Comment:
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a friendly and likable person who is witty and humorous",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.7,
    )

    comment = response.choices[0].message["content"].strip()
    return comment


def get_screen_resolution(device=None):
    """Get the laptop screen resolution using pyautogui."""
    width, height = pyautogui.size()
    print("screen size: ", f"{width}x{height}")
    return width, height


def open_hinge(device=None):
    """
    On laptop, Hinge should already be open in a browser or emulator.
    This is a no-op — the user is expected to have the Hinge window visible.
    """
    print("Laptop mode: Please ensure Hinge is open and visible on your screen.")
    time.sleep(2)
