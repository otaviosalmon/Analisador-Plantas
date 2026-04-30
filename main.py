import cv2
import numpy as np


HSV_GREEN_LOW  = np.array([25,  40,  40])
HSV_GREEN_HIGH = np.array([95, 255, 255])

HSV_YELLOW_LOW  = np.array([15,  40,  40])
HSV_YELLOW_HIGH = np.array([33, 255, 255])

HSV_BROWN_LOW  = np.array([5,  40,  30])
HSV_BROWN_HIGH = np.array([18, 220, 160])

MIN_LEAF_AREA   = 3000
FONT            = cv2.FONT_HERSHEY_SIMPLEX
OVERLAY_ALPHA   = 0.55


STATUS_TABLE = [
    (85, "SAUDÁVEL",   (34, 197,  94)),
    (60, "LEVEMENTE ESTRESSADA", (250, 204,  21)),
    (35, "ESTRESSADA", (249, 115,  22)),
    (  0, "DOENTE",     (239,  68,  68)),
]


def isolate_leaf_mask(hsv):
    green  = cv2.inRange(hsv, HSV_GREEN_LOW,  HSV_GREEN_HIGH)
    yellow = cv2.inRange(hsv, HSV_YELLOW_LOW, HSV_YELLOW_HIGH)
    brown  = cv2.inRange(hsv, HSV_BROWN_LOW,  HSV_BROWN_HIGH)

    combined = cv2.bitwise_or(green, cv2.bitwise_or(yellow, brown))

    kernel = np.ones((5, 5), np.uint8)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN,  kernel, iterations=1)

    return combined, green, yellow, brown


def compute_health_score(green_mask, yellow_mask, brown_mask):
    green_px  = int(np.count_nonzero(green_mask))
    yellow_px = int(np.count_nonzero(yellow_mask))
    brown_px  = int(np.count_nonzero(brown_mask))
    total     = green_px + yellow_px + brown_px

    if total < MIN_LEAF_AREA:
        return None, green_px, yellow_px, brown_px, total

    score = (green_px / total) * 100
    return round(score, 1), green_px, yellow_px, brown_px, total


def resolve_status(score):
    if score is None:
        return "SEM PLANTA DETECTADA", (150, 150, 150)
    for threshold, label, color_rgb in STATUS_TABLE:
        if score >= threshold:
            return label, color_rgb
    return STATUS_TABLE[-1][1], STATUS_TABLE[-1][2]


def draw_bar(frame, score, x, y, bar_w=220, bar_h=18):
    if score is None:
        return
    fill = int(bar_w * score / 100)
    cv2.rectangle(frame, (x, y), (x + bar_w, y + bar_h), (60, 60, 60), -1)
    color = (34, 197, 94) if score >= 60 else (249, 115, 22) if score >= 35 else (239, 68, 68)
    cv2.rectangle(frame, (x, y), (x + fill, y + bar_h), color, -1)
    cv2.rectangle(frame, (x, y), (x + bar_w, y + bar_h), (200, 200, 200), 1)
    cv2.putText(frame, f"{score:.1f}%", (x + bar_w + 8, y + bar_h - 3),
                FONT, 0.48, (220, 220, 220), 1)


def draw_panel(frame, score, label, color_rgb, px_data):
    h, w = frame.shape[:2]
    panel_h = 140
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, panel_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, OVERLAY_ALPHA, frame, 1 - OVERLAY_ALPHA, 0, frame)

    bgr = (color_rgb[2], color_rgb[1], color_rgb[0])

    cv2.putText(frame, "Monitor de Saude de Plantas",
                (12, 24), FONT, 0.6, (200, 200, 200), 1)

    cv2.putText(frame, label, (12, 58), FONT, 0.75, bgr, 2)

    cv2.putText(frame, "Saude foliar:", (12, 84), FONT, 0.45, (180, 180, 180), 1)
    draw_bar(frame, score, 12, 90)

    green_px, yellow_px, brown_px, total = px_data
    if total > 0:
        cv2.putText(frame,
                    f"Verde {green_px}px  Amarelo {yellow_px}px  Marrom {brown_px}px",
                    (12, 128), FONT, 0.38, (160, 160, 160), 1)


def highlight_regions(frame, leaf_mask, green_mask, yellow_mask, brown_mask):
    overlay = frame.copy()

    green_region  = cv2.bitwise_and(frame, frame, mask=green_mask)
    yellow_region = cv2.bitwise_and(frame, frame, mask=yellow_mask)
    brown_region  = cv2.bitwise_and(frame, frame, mask=brown_mask)

    tinted_green  = green_region.copy()
    tinted_yellow = yellow_region.copy()
    tinted_brown  = brown_region.copy()

    tinted_green[green_mask  > 0] = [0, 180, 0]
    tinted_yellow[yellow_mask > 0] = [0, 200, 200]
    tinted_brown[brown_mask  > 0] = [0, 80, 160]

    cv2.addWeighted(tinted_green,  0.35, overlay, 1.0, 0, overlay)
    cv2.addWeighted(tinted_yellow, 0.35, overlay, 1.0, 0, overlay)
    cv2.addWeighted(tinted_brown,  0.35, overlay, 1.0, 0, overlay)

    contours, _ = cv2.findContours(leaf_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) >= MIN_LEAF_AREA:
            cv2.drawContours(overlay, [cnt], -1, (0, 255, 120), 2)

    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Câmera não encontrada.")

    print("Monitor iniciado — pressione [Q] para sair.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        leaf_mask, green_mask, yellow_mask, brown_mask = isolate_leaf_mask(hsv)

        score, g_px, y_px, b_px, total = compute_health_score(
            green_mask, yellow_mask, brown_mask
        )

        label, color_rgb = resolve_status(score)

        highlight_regions(frame, leaf_mask, green_mask, yellow_mask, brown_mask)

        draw_panel(frame, score, label, color_rgb, (g_px, y_px, b_px, total))

        debug = cv2.cvtColor(leaf_mask, cv2.COLOR_GRAY2BGR)
        cv2.putText(debug, "Mascara foliar", (8, 22), FONT, 0.55, (100, 255, 100), 1)
        cv2.imshow("Mascara", debug)

        cv2.imshow("Monitor de Saude de Plantas", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Encerrado.")


if __name__ == "__main__":
    main()
