# app/main.py

import time
import os
import openai
import cv2
import uuid
from dotenv import load_dotenv

# Import your prompt engine weight updater
from prompt_engine import update_template_weights
from config import OPENAI_API_KEY

# Import helper functions (now using pyautogui for laptop control)
from helper_functions import (
    connect_device,
    get_screen_resolution,
    open_hinge,
    swipe,
    capture_screenshot,
    extract_text_from_image,
    do_comparision,
    find_icon,
    generate_comment,
    tap,
    input_text,
)

# Import data store logic for success-rate tracking
from data_store import (
    store_generated_comment,
    store_feedback,
    calculate_template_success_rates,
)

openai.api_key = OPENAI_API_KEY


def main():
    device = connect_device()
    if not device:
        return

    width, height = get_screen_resolution()

    # Approximate coordinates based on screen proportions
    x_select_like_button_approx = int(width * 0.90)
    y_select_like_button_approx = int(height * 0.67)

    x_select_comment_button_approx = int(width * 0.50)
    y_select_comment_button_approx = int(height * 0.75)

    x_select_done_button_approx = int(width * 0.85)
    y_select_done_button_approx = int(height * 0.50)

    x_send_like_button = int(width * 0.75)
    y_send_like_button = int(height * 0.80)

    x_dislike_button_approx = int(width * 0.15)
    y_dislike_button_approx = int(height * 0.85)

    x1_swipe = int(width * 0.15)
    x2_swipe = x1_swipe

    y1_swipe = int(height * 0.5)
    y2_swipe = int(y1_swipe * 0.75)

    # Load sample images for matching criteria (like/dislike)
    like_images = [
        cv2.imread(path) for path in ["images/like2.jpeg"] if os.path.exists(path)
    ]
    dislike_images = [
        cv2.imread(path) for path in ["images/dislike.jpeg"] if os.path.exists(path)
    ]

    open_hinge(device=device)
    time.sleep(5)

    previous_profile_text = ""

    # Optionally, run once at the start: recalc success rates & update template weights
    success_rates = calculate_template_success_rates()
    update_template_weights(success_rates)

    for _ in range(10):
        # Swipe to next profile
        swipe(device, x1_swipe, y1_swipe, x2_swipe, y2_swipe)
        screenshot_path = capture_screenshot(device, "screen")

        # OCR for text extraction
        current_profile_text = extract_text_from_image(screenshot_path).strip()
        if not current_profile_text:
            print("Warning: OCR returned empty text.")

        profile_image = cv2.imread(screenshot_path)

        # Compare with sample images
        match_like = do_comparision(profile_image, like_images)
        match_dislike = do_comparision(profile_image, dislike_images)

        print("Calculated scores => Like:", match_like, "Dislike:", match_dislike)

        # Find the Like button
        x_select_like_button, y_select_like_button = find_icon(
            "images/screen.png",
            "images/heart1.png",
            threshold=0.75,
            min_matches=10,
            approx_x=x_select_like_button_approx,
            approx_y=y_select_like_button_approx,
        )

        # Decision-making logic
        if (
            match_like * 0 < match_dislike
            and x_select_like_button is not None
            and y_select_like_button is not None
        ):
            comment = (
                generate_comment(current_profile_text) or "Hey, I'd love to meet up!"
            )
            print(f"Generated Comment: {comment}")

            comment_id = str(uuid.uuid4())

            store_generated_comment(
                comment_id=comment_id,
                profile_text=current_profile_text,
                generated_comment=comment,
                style_used="unknown",
            )

            # Click Like
            tap(device, x_select_like_button, y_select_like_button)
            print("Like tapped at:", x_select_like_button, y_select_like_button)

        else:
            if (
                previous_profile_text == current_profile_text
                and current_profile_text != ""
            ):
                print("Dislike (same profile encountered again)")
            else:
                print("Dislike (new profile or no like match)")

            print(
                "Dislike tapped at:", x_dislike_button_approx, y_dislike_button_approx
            )
            tap(device, x_dislike_button_approx, y_dislike_button_approx)

        previous_profile_text = current_profile_text
        time.sleep(2)

    # After processing 10 profiles, re-check success rates, update template weights
    success_rates = calculate_template_success_rates()
    update_template_weights(success_rates)
    print("Final success rates:", success_rates)
    print("Main loop finished.")


def test():
    width, height = get_screen_resolution()
    device = connect_device()
    comment = "Hi"

    x_select_comment_button_approx = int(width * 0.50)
    y_select_comment_button_approx = int(height * 0.75)

    swipe(device, width * 0.50, height * 0.70, width * 0.55, height * 0.70)
    tap(device, x_select_comment_button_approx, y_select_comment_button_approx)
    input_text(device, comment)


if __name__ == "__main__":
    main()
