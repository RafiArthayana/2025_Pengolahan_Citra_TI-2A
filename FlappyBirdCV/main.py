import sys, time, random, pygame
from collections import deque
import cv2 as cv, mediapipe as mp

pygame.init()

# Inisialisasi MediaPipe
mp_face_mesh = mp.solutions.face_mesh

# Setup Webcam
VID_CAP = cv.VideoCapture(0)  # Sesuai tes kamu yang sukses
time.sleep(2)  # Tunggu 2 detik agar kamera siap
window_size = (int(VID_CAP.get(cv.CAP_PROP_FRAME_WIDTH)), int(VID_CAP.get(cv.CAP_PROP_FRAME_HEIGHT)))
screen = pygame.display.set_mode(window_size)

# Load Gambar
bird_img = pygame.image.load("bird_sprite.png")
bird_img = pygame.transform.scale(bird_img, (bird_img.get_width() // 12, bird_img.get_height() // 12))
bird_frame = bird_img.get_rect()
bird_frame.center = (window_size[0] // 6, window_size[1] // 2)

pipe_frames = deque()
pipe_img = pygame.image.load("pipe_sprite_single.png")
pipe_template = pipe_img.get_rect()
space_between_pipes = 250

# Inisialisasi Game
game_clock = time.time()
stage = 1
pipeSpawnTimer = 0
time_between_pipe_spawn = 40
dist_between_pipes = 500
pipe_velocity = lambda: dist_between_pipes / time_between_pipe_spawn
score = 0
didUpdateScore = False
game_is_running = True

# Font
font = pygame.font.SysFont("Helvetica Bold.ttf", 50)

with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    while True:
        if not game_is_running:
            over_text = font.render('Game Over!', True, (99, 245, 255))
            tr = over_text.get_rect(center=(window_size[0] // 2, window_size[1] // 2))
            screen.blit(over_text, tr)
            pygame.display.update()
            pygame.time.wait(1000)
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                VID_CAP.release()
                cv.destroyAllWindows()
                pygame.quit()
                sys.exit()

        ret, frame = VID_CAP.read()
        print(ret)  # Cek apakah frame berhasil ditangkap
        if not ret:
            print("Empty frame, skipping...")
            continue

        frame = cv.flip(frame, 1)  # Mirror webcam
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)

        screen.fill((125, 220, 232))

        # Deteksi Wajah
        if results.multi_face_landmarks:
            marker_y = results.multi_face_landmarks[0].landmark[94].y
            bird_frame.centery = (marker_y - 0.5) * 1.5 * window_size[1] + window_size[1] / 2
            bird_frame.top = max(bird_frame.top, 0)
            bird_frame.bottom = min(bird_frame.bottom, window_size[1])

        # Swap axis frame untuk pygame
        frame_display = frame.swapaxes(0, 1)
        pygame.surfarray.blit_array(screen, frame_display)

        # Update posisi pipa
        for pf in pipe_frames:
            pf[0].x -= pipe_velocity()
            pf[1].x -= pipe_velocity()

        if pipe_frames and pipe_frames[0][0].right < 0:
            pipe_frames.popleft()

        # Gambar burung
        screen.blit(bird_img, bird_frame)

        # Gambar pipa dan cek skor
        passed_pipe = True
        for pf in pipe_frames:
            if pf[0].left <= bird_frame.x <= pf[0].right:
                passed_pipe = False
                if not didUpdateScore:
                    score += 1
                    didUpdateScore = True

            screen.blit(pipe_img, pf[1])
            screen.blit(pygame.transform.flip(pipe_img, 0, 1), pf[0])

        if passed_pipe:
            didUpdateScore = False

        # Teks Stage dan Skor
        stage_text = font.render(f'Stage {stage}', True, (99, 245, 255))
        score_text = font.render(f'Score: {score}', True, (99, 245, 255))
        screen.blit(stage_text, (20, 20))
        screen.blit(score_text, (20, 70))

        pygame.display.flip()

        # Cek tabrakan burung dengan pipa
        if any([bird_frame.colliderect(pf[0]) or bird_frame.colliderect(pf[1]) for pf in pipe_frames]):
            game_is_running = False

        # Spawn pipa baru
        if pipeSpawnTimer == 0:
            top_pipe = pipe_template.copy()
            top_pipe.x = window_size[0]
            top_pipe.y = random.randint(-1000, window_size[1] - space_between_pipes - 1000)
            bottom_pipe = pipe_template.copy()
            bottom_pipe.x = window_size[0]
            bottom_pipe.y = top_pipe.y + 1000 + space_between_pipes
            pipe_frames.append([top_pipe, bottom_pipe])

        pipeSpawnTimer += 1
        if pipeSpawnTimer >= time_between_pipe_spawn:
            pipeSpawnTimer = 0

        # Naik level tiap 10 detik
        if time.time() - game_clock >= 10:
            time_between_pipe_spawn *= 5 / 6
            stage += 1
            game_clock = time.time()

# Cleanup
VID_CAP.release()
cv.destroyAllWindows()
pygame.quit()
