from app.helper_functions import (
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


def main():
    device = connect_device()

    if not device:
        return

    width, height = get_screen_resolution()

    # Approximate coordinates based on screen proportions
    x_comment_box = int(width * 0.9)
    y_comment_box = int(height * 0.95)

    x_send = int(width * 0.95)
    y_send = int(width * 0.99)

    x_send_button = int(width * 0.90)
    y_send_button = int(height * 0.89)

    x1_swipe = int(width * 0.15)
    x2_swipe = x1_swipe

    y1_swipe = int(height * 0.5)
    y2_swipe = int(y1_swipe * 0.75)

    text = "Hi, how are you?"

    input_text(device, text)

    tap(device, x_comment_box, y_comment_box)

    swipe(device, width * 0.65, height * 0.82, width * 0.75, height * 0.82)


main()
