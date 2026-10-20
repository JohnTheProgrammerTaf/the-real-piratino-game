import math
import random
import struct
import sys
import pygame

# 1. Inizializzazione sicura con diagnostica audio
pygame.init()
pygame.mixer.quit()  # Resetta eventuali stati precedenti
pygame.mixer.init(frequency=22050, size=-16, channels=1)

# Controlliamo se il mixer è partito correttamente
if pygame.mixer.get_init() is None:
    print(
        "ATTENZIONE: Il mixer audio di Pygame non è riuscito ad avviarsi su"
        " questo computer."
    )
else:
    print("Audio inizializzato con successo:", pygame.mixer.get_init())

schermo = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("The Real Pirate")


# Funzione corretta per generare e convertire il buffer in bytes
def genera_suono_sintetico(tipo):
    sample_rate = 22050
    buffer = bytearray()

    if tipo == "boost":
        durata = 0.25
        for i in range(int(sample_rate * durata)):
            t = i / sample_rate
            freq = 300 + (i * 4)
            val = int(
                16383
                * math.sin(2 * math.pi * freq * t)
                * (1 - i / (sample_rate * durata))
            )
            buffer.extend(struct.pack("<h", val))

    elif tipo == "danno":
        durata = 0.15
        for i in range(int(sample_rate * durata)):
            t = i / sample_rate
            val = int(
                20000
                * math.sin(2 * math.pi * 120 * t)
                * (1 - i / (sample_rate * durata))
            )
            buffer.extend(struct.pack("<h", val))

    elif tipo == "esplosione":
        durata = 0.4
        for i in range(int(sample_rate * durata)):
            val = int(
                random.uniform(-16383, 16383)
                * (1 - i / (sample_rate * durata))
            )
            buffer.extend(struct.pack("<h", val))

    elif tipo == "vittoria":
        durata = 0.4
        note = [523.25, 659.25, 783.99]
        for nota in note:
            for i in range(int(sample_rate * (durata / 3))):
                t = i / sample_rate
                val = int(
                    8000
                    * math.sin(2 * math.pi * nota * t)
                    * (1 - i / (sample_rate * (durata / 3)))
                )
                buffer.extend(struct.pack("<h", val))

    elif tipo == "gameover":
        durata = 0.5
        for i in range(int(sample_rate * durata)):
            t = i / sample_rate
            freq = max(50, 300 - (i * 0.5))
            val = int(
                20000
                * math.sin(2 * math.pi * freq * t)
                * (1 - i / (sample_rate * durata))
            )
            buffer.extend(struct.pack("<h", val))

    return pygame.mixer.Sound(bytes(buffer))


# Generatore della OST originale di "Drunken Sailor" per il Title Screen
def genera_ost_title_screen():
    sample_rate = 22050
    buffer = bytearray()
    
    melodia_originale = [
        (293.66, 0.35), (293.66, 0.35), (293.66, 0.35), (293.66, 0.35),
        (293.66, 0.35), (349.23, 0.35), (440.00, 0.70), (293.66, 0.35),
        (261.63, 0.35), (261.63, 0.35), (261.63, 0.35), (261.63, 0.35),
        (261.63, 0.35), (329.63, 0.35), (392.00, 0.70), (261.63, 0.35),
        (293.66, 0.35), (293.66, 0.35), (349.23, 0.35), (440.00, 0.35),
        (523.25, 0.70), (440.00, 0.35), (392.00, 0.35), (329.63, 0.35),
        (293.66, 0.50), (392.00, 0.50), (293.66, 1.20), (0, 0.8)
    ]

    for freq, durata in melodia_originale:
        num_samples = int(sample_rate * durata)
        for i in range(num_samples):
            t = i / sample_rate
            if freq == 0:
                val = 0
            else:
                sin_wave = math.sin(2 * math.pi * freq * t)
                inviluppo = 1 - (i / num_samples) ** 0.5
                val = int(4000 * sin_wave * inviluppo)
            buffer.extend(struct.pack("<h", val))

    return pygame.mixer.Sound(bytes(buffer))


# Generatore di 5 varianti della OST con ritmica cadenzata per i livelli di gioco
def genera_varianti_ost():
    sample_rate = 22050
    playlist = []

    strutture_varianti = [
        [
            [(293.66, 0.25), (293.66, 0.25), (293.66, 0.25), (293.66, 0.25), (293.66, 0.25), (349.23, 0.25), (440.00, 0.50), (293.66, 0.50), (0, 0.20)],
            [(261.63, 0.25), (261.63, 0.25), (261.63, 0.25), (261.63, 0.25), (329.63, 0.25), (392.00, 0.25), (329.63, 0.50), (261.63, 0.50), (0, 0.20)],
            [(293.66, 0.25), (349.23, 0.25), (440.00, 0.25), (523.25, 0.50), (440.00, 0.25), (392.00, 0.25), (349.23, 0.50), (293.66, 1.20), (0, 1.00)]
        ],
        [
            [(329.63, 0.25), (329.63, 0.25), (329.63, 0.25), (329.63, 0.25), (392.00, 0.25), (440.00, 0.25), (523.25, 0.50), (392.00, 0.50), (0, 0.20)],
            [(392.00, 0.25), (392.00, 0.25), (392.00, 0.25), (392.00, 0.25), (440.00, 0.25), (523.25, 0.25), (587.33, 0.50), (523.25, 0.50), (0, 0.20)],
            [(440.00, 0.25), (392.00, 0.25), (349.23, 0.25), (329.63, 0.50), (293.66, 0.50), (261.63, 1.20), (0, 1.00)]
        ],
        [
            [(220.00, 0.30), (220.00, 0.30), (220.00, 0.30), (220.00, 0.30), (246.94, 0.30), (261.63, 0.30), (293.66, 0.60), (220.00, 0.60), (0, 0.20)],
            [(261.63, 0.30), (261.63, 0.30), (261.63, 0.30), (293.66, 0.30), (329.63, 0.30), (349.23, 0.60), (329.63, 0.60), (0, 0.20)],
            [(293.66, 0.30), (261.63, 0.30), (246.94, 0.30), (220.00, 0.60), (196.00, 0.60), (220.00, 1.50), (0, 1.00)]
        ],
        [
            [(349.23, 0.25), (349.23, 0.25), (392.00, 0.25), (392.00, 0.25), (440.00, 0.25), (493.88, 0.25), (523.25, 0.50), (440.00, 0.50), (0, 0.20)],
            [(440.00, 0.25), (440.00, 0.25), (493.88, 0.25), (493.88, 0.25), (523.25, 0.25), (587.33, 0.25), (523.25, 0.50), (440.00, 0.50), (0, 0.20)],
            [(392.00, 0.25), (349.23, 0.25), (329.63, 0.25), (349.23, 0.50), (293.66, 0.50), (349.23, 1.20), (0, 1.00)]
        ],
        [
            [(392.00, 0.25), (392.00, 0.25), (440.00, 0.25), (440.00, 0.25), (523.25, 0.25), (587.33, 0.25), (523.25, 0.50), (392.00, 0.50), (0, 0.20)],
            [(440.00, 0.25), (440.00, 0.25), (523.25, 0.25), (523.25, 0.25), (587.33, 0.25), (659.25, 0.25), (587.33, 0.50), (440.00, 0.50), (0, 0.20)],
            [(349.23, 0.25), (329.63, 0.25), (293.66, 0.25), (392.00, 0.50), (329.63, 0.50), (293.66, 1.40), (0, 1.00)]
        ]
    ]

    for strofe in strutture_varianti:
        buffer = bytearray()
        durata_totale_campioni = 0
        parsed_sequence = []
        
        for strofa in strofe:
            for freq, durata in strofa:
                num_samples = int(sample_rate * durata)
                parsed_sequence.append((freq, num_samples))
                durata_totale_campioni += num_samples

        campioni_emessi = 0
        for idx_nota, (freq, num_samples) in enumerate(parsed_sequence):
            for i in range(num_samples):
                t = i / sample_rate
                if freq == 0:
                    val = 0
                else:
                    sin_wave = math.sin(2 * math.pi * freq * t)
                    inviluppo = 1 - (i / num_samples) ** 0.6
                    if idx_nota == 0 and i < 800:
                        inviluppo *= (i / 800)
                    val = int(3500 * sin_wave * inviluppo)

                campioni_rimanenti = durata_totale_campioni - campioni_emessi
                if campioni_rimanenti < sample_rate * 1.5:
                    fattore_fadeout = campioni_rimanenti / (sample_rate * 1.5)
                    val = int(val * fattore_fadeout)

                buffer.extend(struct.pack("<h", val))
                campioni_emessi += 1

        playlist.append(pygame.mixer.Sound(bytes(buffer)))

    return playlist


# Generazione dei suoni e della playlist
suono_boost = genera_suono_sintetico("boost")
suono_danno = genera_suono_sintetico("danno")
suono_esplosione = genera_suono_sintetico("esplosione")
suono_vittoria = genera_suono_sintetico("vittoria")
suono_gameover = genera_suono_sintetico("gameover")

ost_title = genera_ost_title_screen()
playlist_ost = genera_varianti_ost()
ost_corrente = None


def play_suono(suono):
    if suono:
        suono.play()


# Colori
COLORE_MARE = (20, 100, 200)
COLORE_SCAFO = (139, 69, 19)
COLORE_BORDO_SCAFO = (80, 40, 10)
COLORE_VELA = (255, 255, 255)
COLORE_BORDO_VELA = (180, 180, 180)
COLORE_VENTO = (200, 230, 255)
COLORE_TESTO = (255, 255, 255)
COLORE_SABBIA = (238, 203, 173)
COLORE_VERDE = (34, 139, 34)
COLORE_SCOGLIO = (112, 128, 144)
COLORE_BORDO_SCOGLIO = (50, 60, 70)
COLORE_PORTO_A = (218, 165, 32)
COLORE_PORTO_B_BASE = (100, 110, 120)
COLORE_PORTO_B_LEGNO = (160, 82, 45)
COLORE_BARILE = (101, 67, 33)
COLORE_CERCHIO_BARILE = (50, 30, 10)
COLORE_BARILE_ROSSO = (220, 20, 60)
COLORE_VITA = (255, 50, 50)
COLORE_BOOST = (0, 220, 255)

# Direzioni del Vento
vento_8_direzioni = [
    ("NORD", 0),
    ("NORD-EST", 45),
    ("EST", 90),
    ("SUD-EST", 135),
    ("SUD", 180),
    ("SUD-OVEST", 225),
    ("OVEST", 270),
    ("NORD-OVEST", 315)
]

livello_gioco = 1
stato_schermata = "TITLE"
punteggio_totale = 0
punteggio_aggiunto_questo_livello = False
gioco_completato = False


def ottieni_pip_massimi(lvl):
    if lvl < 10:
        return 1
    elif lvl < 20:
        return 2
    else:
        return 3


def inizializza_gioco(reset_totale=False):
    global barca_x, barca_y, angolo_barca, velocita_corrente, angolo_vela_visuale
    global vento_corrente, nome_vento, angolo_vento, forza_vento_livello
    global tempo_ultimo_cambio, prossimo_cambio_intervallo
    global porto_a_pos, porto_b
    global isole, scogli, barili, gioco_vinto, barca_distrutta, motivo_sconfitta
    global vite_barca, tempo_ultimo_danno, livello_gioco
    global tempo_limite_partenza, tempo_inizio_partenza, timer_avviato
    global pip_boost, pip_boost_massimi, tempo_fine_boost, evento_fine_suonato
    global ost_corrente, punteggio_totale, punteggio_aggiunto_questo_livello, gioco_completato

    if reset_totale:
        livello_gioco = 1
        punteggio_totale = 0
        gioco_completato = False

    punteggio_aggiunto_questo_livello = False
    pip_boost_massimi = ottieni_pip_massimi(livello_gioco)
    pip_boost = pip_boost_massimi
    tempo_fine_boost = 0
    evento_fine_suonato = False

    rx_a = random.randint(80, 250)
    ry_a = random.randint(150, 550)
    porto_a_pos = (rx_a, ry_a)

    barca_x = porto_a_pos[0]
    barca_y = porto_a_pos[1]
    angolo_barca = 0
    velocita_corrente = 0.0
    timer_avviato = False

    rx_b = random.randint(750, 920)
    ry_b = random.randint(150, 550)
    porto_b = {"pos": (rx_b, ry_b), "raggio": 55}

    vite_barca = 3
    tempo_ultimo_danno = 0
    motivo_sconfitta = ""

    if livello_gioco < 10:
        secondi_assegnati = 20
    elif livello_gioco < 20:
        secondi_assegnati = 15
    else:
        secondi_assegnati = 10

    tempo_limite_partenza = secondi_assegnati * 1000
    tempo_inizio_partenza = 0

    vento_corrente = random.choice(vento_8_direzioni)
    nome_vento, angolo_vento = vento_corrente
    angolo_vela_visuale = float(angolo_vento)

    if livello_gioco < 10:
        forza_vento_livello = random.randint(1, 4)
    elif livello_gioco < 19:
        forza_vento_livello = random.randint(1, 5)
    else:
        forza_vento_livello = random.randint(1, 6)

    tempo_ultimo_cambio = pygame.time.get_ticks()
    prossimo_cambio_intervallo = random.randint(2, 5) * 1000

    num_isole = min(8, 3 + max(0, livello_gioco - 1) // 2)
    num_scogli = min(14, 4 + max(0, livello_gioco - 1) // 2)

    isole = []
    for _ in range(num_isole):
        tentativi = 0
        while tentativi < 100:
            rx = random.randint(280, 720)
            ry = random.randint(130, 570)
            dist_a = math.hypot(rx - porto_a_pos[0], ry - porto_a_pos[1])
            dist_b = math.hypot(rx - porto_b["pos"][0], ry - porto_b["pos"][1])
            sovrapposta = False
            for isola_esistente in isole:
                if math.hypot(rx - isola_esistente["pos"][0], ry - isola_esistente["pos"][1]) < isola_esistente["raggio"] + 45:
                    sovrapposta = True
            if dist_a > 130 and dist_b > 130 and not sovrapposta:
                isole.append({"pos": (rx, ry), "raggio": random.randint(30, 50)})
                break
            tentativi += 1

    scogli = []
    for _ in range(num_scogli):
        tentativi = 0
        while tentativi < 100:
            rx = random.randint(150, 850)
            ry = random.randint(100, 600)
            dist_a = math.hypot(rx - porto_a_pos[0], ry - porto_a_pos[1])
            dist_b = math.hypot(rx - porto_b["pos"][0], ry - porto_b["pos"][1])
            sovrapposto = False
            for isola in isole:
                if math.hypot(rx - isola["pos"][0], ry - isola["pos"][1]) < isola["raggio"] + 25:
                    sovrapposto = True
            for scoglio_esistente in scogli:
                if math.hypot(rx - scoglio_esistente["pos"][0], ry - scoglio_esistente["pos"][1]) < 35:
                    sovrapposto = True
            if dist_a > 90 and dist_b > 90 and not sovrapposto:
                scogli.append({"pos": (rx, ry), "raggio": random.randint(14, 24)})
                break
            tentativi += 1

    num_barili = min(12, 6 + (livello_gioco // 3))
    barili = []
    for _ in range(num_barili):
        while True:
            rx = random.randint(50, 950)
            ry = random.randint(50, 650)
            if math.hypot(rx - porto_a_pos[0], ry - porto_a_pos[1]) > 80 and math.hypot(rx - porto_b["pos"][0], ry - porto_b["pos"][1]) > 80:
                is_rosso = (random.random() < 0.28)
                barili.append({
                    "x": rx, "y": ry, "raggio": 16,
                    "velocita_extra": random.uniform(0.7, 1.5),
                    "fase_zigzag": random.uniform(0, 6.28), "rosso": is_rosso
                })
                break

    gioco_vinto = False
    barca_distrutta = False

    if stato_schermata == "GIOCO":
        if ost_corrente:
            ost_corrente.stop()
        ost_corrente = random.choice(playlist_ost)
        ost_corrente.play(loops=-1)


accelerazione = 0.05
attrito = 0.985

inizializza_gioco(reset_totale=True)

orologio = pygame.time.Clock()
font = pygame.font.SysFont(None, 22)
font_comando = pygame.font.SysFont(None, 20, bold=True)
font_grande = pygame.font.SysFont(None, 30, bold=True)
font_timer = pygame.font.SysFont(None, 52, bold=True)
font_titolo = pygame.font.SysFont(None, 48, bold=True)

gioco_attivo = True

ost_title.play(loops=-1)

while gioco_attivo:
    tempo_attuale = pygame.time.get_ticks()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            gioco_attivo = False
        elif evento.type == pygame.KEYDOWN:
            if stato_schermata == "TITLE":
                if evento.key == pygame.K_RETURN:
                    stato_schermata = "ISTRUZIONI"
            elif stato_schermata == "ISTRUZIONI":
                if evento.key == pygame.K_RETURN:
                    if ost_title:
                        ost_title.stop()
                    stato_schermata = "GIOCO"
                    inizializza_gioco(reset_totale=True)
            elif stato_schermata == "GIOCO":
                if evento.key == pygame.K_RETURN:
                    if gioco_completato:
                        stato_schermata = "TITLE"
                        ost_title.play(loops=-1)
                        inizializza_gioco(reset_totale=True)
                    elif gioco_vinto:
                        livello_gioco += 1
                        inizializza_gioco(reset_totale=False)
                    elif barca_distrutta:
                        inizializza_gioco(reset_totale=True)
                    else:
                        inizializza_gioco(reset_totale=False)
                elif evento.key == pygame.K_SPACE:
                    if not gioco_vinto and not barca_distrutta and not gioco_completato:
                        if pip_boost > 0 and tempo_attuale > tempo_fine_boost:
                            if not timer_avviato:
                                timer_avviato = True
                                tempo_inizio_partenza = tempo_attuale
                            pip_boost -= 1
                            tempo_fine_boost = tempo_attuale + 1000
                            play_suono(suono_boost)

    # --- TITLE SCREEN ---
    if stato_schermata == "TITLE":
        schermo.fill((10, 25, 45))

        t_titolo = font_titolo.render("THE REAL PIRATE", True, (255, 215, 0))
        schermo.blit(t_titolo, t_titolo.get_rect(center=(500, 260)).topleft)

        font_sottotitolo = pygame.font.SysFont(None, 28)
        t_sottotitolo = font_sottotitolo.render("Inizia l'avventura di Captain CIRZ Morgan", True, (200, 220, 240))
        schermo.blit(t_sottotitolo, t_sottotitolo.get_rect(center=(500, 330)).topleft)

        if (tempo_attuale // 400) % 2 == 0:
            t_start = font_grande.render("PRESS START [ENTER]", True, (255, 255, 255))
            schermo.blit(t_start, t_start.get_rect(center=(500, 430)).topleft)

        pygame.display.flip()
        orologio.tick(60)
        continue

    # --- SCHERMATA ISTRUZIONI ---
    if stato_schermata == "ISTRUZIONI":
        schermo.fill((15, 30, 50))

        titolo = font_titolo.render("THE REAL PIRATE - COMANDI DI GIOCO", True, (255, 215, 0))
        schermo.blit(titolo, titolo.get_rect(center=(500, 60)))

        comandi = [
            ("FRECCIA SINISTRA / DESTRA", "Ruota il timone della barca"),
            ("FRECCIA SU", "Aumenta le vele e accelera"),
            ("BARRA SPAZIATRICE", "Boost: Velocità + Invulnerabilità ad ostacoli/barili"),
            ("TASTO [ENTER]", "Avvia la partita / Passa al livello successivo"),
            ("OBIETTIVO GIOCO", "Raggiungi il Porto B prima dello scadere del tempo!"),
            ("ATTENZIONE!", "I barili rossi ti tolgono una vita e ti fanno respawnare al Porto A!")
        ]

        y_offset = 140
        for tasto, desc in comandi:
            box_tasto = pygame.Surface((340, 50), pygame.SRCALPHA)
            box_tasto.fill((255, 255, 255, 20))
            schermo.blit(box_tasto, (40, y_offset))

            box_desc = pygame.Surface((570, 50), pygame.SRCALPHA)
            box_desc.fill((255, 255, 255, 20))
            schermo.blit(box_desc, (390, y_offset))

            t_tasto = font_comando.render(tasto, True, (0, 220, 255))
            t_desc = font.render(desc, True, (255, 255, 255))
            
            schermo.blit(t_tasto, (50, y_offset + 16))
            schermo.blit(t_desc, (405, y_offset + 15))

            y_offset += 65

        t_start = font_grande.render("Premi [ENTER] per salpare!", True, (255, 255, 0))
        schermo.blit(t_start, t_start.get_rect(center=(500, 635)).topleft)

        pygame.display.flip()
        orologio.tick(60)
        continue

    # --- SCHERMATA DI GIOCO ---
    boost_attivo = (tempo_attuale < tempo_fine_boost)
    tasti = pygame.key.get_pressed()

    diff_vela = (angolo_vento - angolo_vela_visuale + 180) % 360 - 180
    angolo_vela_visuale += diff_vela * 0.05

    if not gioco_vinto and not barca_distrutta and not gioco_completato:
        if not timer_avviato and (tasti[pygame.K_LEFT] or tasti[pygame.K_RIGHT] or tasti[pygame.K_UP]):
            timer_avviato = True
            tempo_inizio_partenza = tempo_attuale

        if timer_avviato:
            tempo_trascorso_livello = tempo_attuale - tempo_inizio_partenza
            tempo_rimanente_livello = max(0, int((tempo_limite_partenza - tempo_trascorso_livello) / 1000))

            if tempo_trascorso_livello > tempo_limite_partenza:
                barca_distrutta = True
                motivo_sconfitta = "tempo_scaduto"
        else:
            if livello_gioco < 10:
                tempo_rimanente_livello = 20
            elif livello_gioco < 20:
                tempo_rimanente_livello = 15
            else:
                tempo_rimanente_livello = 10

    if not gioco_vinto and not barca_distrutta and not gioco_completato:
        if tempo_attuale - tempo_ultimo_cambio > prossimo_cambio_intervallo:
            nuovo_vento = random.choice(vento_8_direzioni)
            while nuovo_vento == vento_corrente:
                nuovo_vento = random.choice(vento_8_direzioni)

            vento_corrente = nuovo_vento
            nome_vento, angolo_vento = vento_corrente

            if livello_gioco < 10:
                forza_vento_livello = random.randint(1, 4)
            elif livello_gioco < 19:
                forza_vento_livello = random.randint(1, 5)
            else:
                forza_vento_livello = random.randint(1, 6)

            tempo_ultimo_cambio = tempo_attuale
            prossimo_cambio_intervallo = random.randint(2, 5) * 1000

    tempo_vento_rimanente = max(0, int((prossimo_cambio_intervallo - (tempo_attuale - tempo_ultimo_cambio)) / 1000))

    if not gioco_vinto and not barca_distrutta and not gioco_completato:
        if tasti[pygame.K_LEFT]:
            angolo_barca -= 3
        if tasti[pygame.K_RIGHT]:
            angolo_barca += 3

        angolo_barca = angolo_barca % 360
        differenza_angolo = abs((angolo_barca - angolo_vento + 180) % 360 - 180)

        if boost_attivo:
            max_velocita = 4.5
            stato_vela = "✨ BOOST ATTIVO!"
        else:
            if differenza_angolo < 45:
                max_velocita = 4.0 + (forza_vento_livello * 0.3)
                stato_vela = "Vento in Poppa!"
            elif differenza_angolo > 135:
                if forza_vento_livello == 5:
                    max_velocita = 0.05  # Consente solo un impercettibile avanzamento di inerzia senza spinta opposta
                    stato_vela = "TEMPESTA LVL 5: Accelerazione bloccata!"
                elif forza_vento_livello == 6:
                    max_velocita = 0.8
                    stato_vela = "TEMPESTA LVL 6: Deriva forzata!"
                else:
                    max_velocita = max(0.2, 1.5 - (forza_vento_livello * 0.25))
                    stato_vela = "Controvento!"
            else:
                max_velocita = 2.5
                stato_vela = "Vento di Traverso"

        if tasti[pygame.K_UP]:
            if not boost_attivo and forza_vento_livello == 5 and differenza_angolo > 135:
                velocita_corrente *= attrito
            elif velocita_corrente < max_velocita:
                velocita_corrente += accelerazione
        else:
            velocita_corrente *= attrito
            if velocita_corrente < 0.05:
                velocita_corrente = 0.0

        if velocita_corrente > 0:
            rad_barca = math.radians(angolo_barca)
            barca_x += velocita_corrente * math.sin(rad_barca)
            barca_y -= velocita_corrente * math.cos(rad_barca)

        # Spinta passiva del vento applicata solo se NON siamo a forza 5 in pieno controvento
        if timer_avviato and not boost_attivo:
            applica_spinta_vento = True
            if forza_vento_livello == 5 and differenza_angolo > 135:
                applica_spinta_vento = False  # Il forza 5 blocca la spinta opposta

            if applica_spinta_vento:
                rad_vento = math.radians(angolo_vento)
                fattore_forza = 0.35 if forza_vento_livello == 6 else (0.2 * forza_vento_livello)
                barca_x += fattore_forza * math.sin(rad_vento)
                barca_y -= fattore_forza * math.cos(rad_vento)

        # --- MOVIMENTO BARILI ---
        nuovi_barili_da_aggiungere = []
        rad_vento_barili = math.radians(angolo_vento)

        for barile in barili[:]:
            barile["fase_zigzag"] += 0.05
            spinta_barile = (0.3 + (forza_vento_livello * 0.15)) * barile["velocita_extra"]

            angolo_perpendicolare = rad_vento_barili + math.pi / 2
            forza_zigzag = math.sin(barile["fase_zigzag"]) * 0.8

            barile["x"] += spinta_barile * math.sin(rad_vento_barili) + forza_zigzag * math.cos(angolo_perpendicolare)
            barile["y"] -= spinta_barile * math.cos(rad_vento_barili) - forza_zigzag * math.sin(angolo_perpendicolare)

            for isola in isole:
                dist_i = math.hypot(barile["x"] - isola["pos"][0], barile["y"] - isola["pos"][1])
                if dist_i < isola["raggio"] + barile["raggio"]:
                    ang_urt = math.atan2(barile["y"] - isola["pos"][1], barile["x"] - isola["pos"][0])
                    barile["x"] = isola["pos"][0] + math.cos(ang_urt) * (isola["raggio"] + barile["raggio"] + 2)
                    barile["y"] = isola["pos"][1] + math.sin(ang_urt) * (isola["raggio"] + barile["raggio"] + 2)

            for scoglio in scogli:
                dist_s = math.hypot(barile["x"] - scoglio["pos"][0], barile["y"] - scoglio["pos"][1])
                if dist_s < scoglio["raggio"] + barile["raggio"]:
                    ang_urt = math.atan2(barile["y"] - scoglio["pos"][1], barile["x"] - scoglio["pos"][0])
                    barile["x"] = scoglio["pos"][0] + math.cos(ang_urt) * (scoglio["raggio"] + barile["raggio"] + 2)
                    barile["y"] = scoglio["pos"][1] + math.sin(ang_urt) * (scoglio["raggio"] + barile["raggio"] + 2)

            for altro_barile in barili:
                if barile != altro_barile:
                    dist_b = math.hypot(barile["x"] - altro_barile["x"], barile["y"] - altro_barile["y"])
                    if dist_b < barile["raggio"] * 2:
                        ang_b = math.atan2(barile["y"] - altro_barile["y"], barile["x"] - altro_barile["x"])
                        barile["x"] += math.cos(ang_b) * 1.5
                        barile["y"] += math.sin(ang_b) * 1.5

            uscito = False
            bordo_uscita = ""
            if barile["x"] < -30:
                uscito = True; bordo_uscita = "sinistra"
            elif barile["x"] > 1030:
                uscito = True; bordo_uscita = "destra"
            elif barile["y"] < -30:
                uscito = True; bordo_uscita = "sopra"
            elif barile["y"] > 730:
                uscito = True; bordo_uscita = "sotto"

            if uscito:
                barili.remove(barile)
                quanti_nuovi = random.randint(0, 3)
                for _ in range(quanti_nuovi):
                    if bordo_uscita == "sinistra":
                        nx = 990; ny = random.randint(50, 650)
                    elif bordo_uscita == "destra":
                        nx = 10; ny = random.randint(50, 650)
                    elif bordo_uscita == "sopra":
                        nx = random.randint(50, 950); ny = 670
                    else:
                        nx = random.randint(50, 950); ny = 30

                    is_rosso = (random.random() < 0.28)
                    nuovi_barili_da_aggiungere.append({
                        "x": nx, "y": ny, "raggio": 16,
                        "velocita_extra": random.uniform(0.7, 1.4),
                        "fase_zigzag": random.uniform(0, 6.28), "rosso": is_rosso
                    })

        barili.extend(nuovi_barili_da_aggiungere)

    # --- COLLISIONI BARCA ---
    dist_b = math.hypot(barca_x - porto_b["pos"][0], barca_y - porto_b["pos"][1])
    if dist_b < porto_b["raggio"] and not barca_distrutta and not gioco_vinto:
        gioco_vinto = True
        velocita_corrente = 0.0

        if not punteggio_aggiunto_questo_livello:
            if livello_gioco < 10:
                moltiplicatore = 1.0
            elif livello_gioco < 20:
                moltiplicatore = 1.5
            else:
                moltiplicatore = 2.0

            punteggio_livello = int(tempo_rimanente_livello * 10 * moltiplicatore)
            punteggio_totale += punteggio_livello
            punteggio_aggiunto_questo_livello = True

        if livello_gioco >= 30:
            gioco_completato = True

        dx = barca_x - porto_b["pos"][0]
        dy = barca_y - porto_b["pos"][1]
        angolo_urto = math.atan2(dy, dx)
        barca_x = porto_b["pos"][0] + math.cos(angolo_urto) * porto_b["raggio"]
        barca_y = porto_b["pos"][1] + math.sin(angolo_urto) * porto_b["raggio"]

    if not gioco_vinto and not barca_distrutta and not gioco_completato:
        def applica_danno():
            global vite_barca, barca_distrutta, tempo_ultimo_danno, motivo_sconfitta
            if tempo_attuale - tempo_ultimo_danno > 1000:
                vite_barca -= 1
                tempo_ultimo_danno = tempo_attuale
                play_suono(suono_danno)
                if vite_barca <= 0:
                    barca_distrutta = True
                    motivo_sconfitta = "avaria"

        if not boost_attivo:
            for isola in isole:
                dist_isola = math.hypot(barca_x - isola["pos"][0], barca_y - isola["pos"][1])
                if dist_isola < isola["raggio"]:
                    applica_danno()
                    velocita_corrente = 0.0
                    dx = barca_x - isola["pos"][0]
                    dy = barca_y - isola["pos"][1]
                    angolo_urto = math.atan2(dy, dx)
                    barca_x = isola["pos"][0] + math.cos(angolo_urto) * isola["raggio"]
                    barca_y = isola["pos"][1] + math.sin(angolo_urto) * isola["raggio"]

            for scoglio in scogli:
                dist_scoglio = math.hypot(barca_x - scoglio["pos"][0], barca_y - scoglio["pos"][1])
                if dist_scoglio < scoglio["raggio"]:
                    applica_danno()
                    velocita_corrente = 0.0
                    dx = barca_x - scoglio["pos"][0]
                    dy = barca_y - scoglio["pos"][1]
                    angolo_urto = math.atan2(dy, dx)
                    barca_x = scoglio["pos"][0] + math.cos(angolo_urto) * scoglio["raggio"]
                    barca_y = scoglio["pos"][1] + math.sin(angolo_urto) * scoglio["raggio"]

        for barile in barili:
            dist_barile = math.hypot(barca_x - barile["x"], barca_y - barile["y"])
            somma_raggi = barile["raggio"] + 15
            if dist_barile < somma_raggi:
                if barile["rosso"]:
                    if tempo_attuale - tempo_ultimo_danno > 1000:
                        vite_barca -= 1
                        tempo_ultimo_danno = tempo_attuale
                        play_suono(suono_esplosione)
                        barca_x = porto_a_pos[0]
                        barca_y = porto_a_pos[1]
                        velocita_corrente = 0.0
                        barili.remove(barile)
                        if vite_barca <= 0:
                            barca_distrutta = True
                            motivo_sconfitta = "avaria"
                elif not boost_attivo:
                    applica_danno()
                    dx = barca_x - barile["x"]
                    dy = barca_y - barile["y"]
                    angolo_urto = math.atan2(dy, dx)
                    velocita_corrente *= 0.2
                    barca_x = barile["x"] + math.cos(angolo_urto) * somma_raggi
                    barca_y = barile["y"] + math.sin(angolo_urto) * somma_raggi
                    barile["x"] -= math.cos(angolo_urto) * 8
                    barile["y"] -= math.sin(angolo_urto) * 8

    barca_x = max(20, min(barca_x, 980))
    barca_y = max(60, min(barca_y, 600))

    # GESTIONE AUDIO SUCCESSO / SCONFITTA
    if (gioco_vinto or barca_distrutta or gioco_completato) and not evento_fine_suonato:
        if ost_corrente:
            ost_corrente.stop()
        if gioco_vinto or gioco_completato:
            play_suono(suono_vittoria)
        else:
            play_suono(suono_gameover)
        evento_fine_suonato = True

    # --- 4. GRAFICA ---
    schermo.fill(COLORE_MARE)

    rad_v = math.radians(angolo_vento)
    lunghezza_linea = 15 + (forza_vento_livello * 8)
    dx_v = math.sin(rad_v) * lunghezza_linea
    dy_v = -math.cos(rad_v) * lunghezza_linea
    for px in range(50, 1000, 150):
        for py in range(60, 600, 120):
            pygame.draw.line(schermo, COLORE_VENTO, (px, py), (px + dx_v, py + dy_v), 2)
            pygame.draw.circle(schermo, COLORE_VENTO, (int(px + dx_v), int(py + dy_v)), 3)

    pygame.draw.circle(schermo, COLORE_PORTO_A, porto_a_pos, 25, 4)
    t_a = font.render("PORTO A", True, COLORE_TESTO)
    schermo.blit(t_a, (porto_a_pos[0] - 30, porto_a_pos[1] + 32))

    bx, by = porto_b["pos"]
    pygame.draw.circle(schermo, COLORE_PORTO_B_LEGNO, (bx, by), porto_b["raggio"])
    pygame.draw.circle(schermo, COLORE_PORTO_B_BASE, (bx, by), porto_b["raggio"] - 12)
    pygame.draw.circle(schermo, (255, 215, 0), (bx, by), 10)
    t_b = font.render("ARRIVO (B)", True, (255, 255, 255))
    schermo.blit(t_b, (bx - 42, by - 40))

    for isola in isole:
        pygame.draw.circle(schermo, COLORE_SABBIA, isola["pos"], isola["raggio"])
        pygame.draw.circle(schermo, COLORE_VERDE, isola["pos"], isola["raggio"] - 12)

    for scoglio in scogli:
        pygame.draw.circle(schermo, COLORE_SCOGLIO, scoglio["pos"], scoglio["raggio"])
        pygame.draw.circle(schermo, COLORE_BORDO_SCOGLIO, scoglio["pos"], scoglio["raggio"], 2)

    for barile in barili:
        bx_b, by_b = int(barile["x"]), int(barile["y"])
        if barile["rosso"]:
            pygame.draw.circle(schermo, COLORE_BARILE_ROSSO, (bx_b, by_b), barile["raggio"])
            pygame.draw.circle(schermo, (100, 0, 0), (bx_b, by_b), barile["raggio"], 2)
            pygame.draw.line(schermo, (255, 255, 255), (bx_b - 6, by_b), (bx_b + 6, by_b), 3)
            pygame.draw.line(schermo, (255, 255, 255), (bx_b, by_b - 6), (bx_b, by_b + 6), 3)
        else:
            pygame.draw.circle(schermo, COLORE_BARILE, (bx_b, by_b), barile["raggio"])
            pygame.draw.circle(schermo, COLORE_CERCHIO_BARILE, (bx_b, by_b), barile["raggio"], 2)
            pygame.draw.line(schermo, COLORE_CERCHIO_BARILE, (bx_b - 10, by_b), (bx_b + 10, by_b), 2)

    in_invulnerabilita = (tempo_attuale - tempo_ultimo_danno < 1000)
    mostra_barca = not in_invulnerabilita or ((tempo_attuale // 100) % 2 == 0)

    if not barca_distrutta and mostra_barca and not gioco_completato:
        if boost_attivo:
            pygame.draw.circle(schermo, COLORE_BOOST, (int(barca_x), int(barca_y)), 35, 2)

        barca_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        punti_scafo = [(30, 8), (38, 48), (22, 48)]
        pygame.draw.polygon(barca_surf, COLORE_SCAFO, punti_scafo)
        pygame.draw.polygon(barca_surf, COLORE_BORDO_SCAFO, punti_scafo, 2)

        scafo_ruotato = pygame.transform.rotate(barca_surf, -angolo_barca)
        rect_scafo = scafo_ruotato.get_rect(center=(int(barca_x), int(barca_y)))
        schermo.blit(scafo_ruotato, rect_scafo.topleft)

        vela_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        punti_vela = [(30, 10), (18, 48), (42, 48)]
        pygame.draw.polygon(vela_surf, COLORE_VELA, punti_vela)
        pygame.draw.polygon(vela_surf, COLORE_BORDO_VELA, punti_vela, 2)

        vela_ruotata = pygame.transform.rotate(vela_surf, -angolo_vela_visuale)
        rect_vela = vela_ruotata.get_rect(center=(int(barca_x), int(barca_y)))
        schermo.blit(vela_ruotata, rect_vela.topleft)
    elif barca_distrutta:
        pygame.draw.circle(schermo, (255, 69, 0), (int(barca_x), int(barca_y)), 25)
        pygame.draw.circle(schermo, (255, 215, 0), (int(barca_x), int(barca_y)), 15)

    # --- BARRA SUPERIORE (UI TOP) ---
    barra_top = pygame.Surface((1000, 50), pygame.SRCALPHA)
    barra_top.fill((0, 0, 0, 180))
    schermo.blit(barra_top, (0, 0))

    str_forza = "█" * forza_vento_livello + "░" * (6 - forza_vento_livello)
    colore_hud = (255, 80, 80) if forza_vento_livello >= 5 else COLORE_TESTO

    t1 = font.render(f"Vento: {nome_vento} (Tra {tempo_vento_rimanente}s) | Forza: [{str_forza}] (Lvl {forza_vento_livello}/6)", True, colore_hud)
    t2 = font.render(f"Stato: {stato_vela} | Vel: {round(velocita_corrente, 1)} nodi", True, COLORE_TESTO)
    schermo.blit(t1, (20, 8))
    schermo.blit(t2, (20, 28))

    t_vite = font.render("Vite:", True, COLORE_TESTO)
    schermo.blit(t_vite, (600, 16))
    for i in range(3):
        pos_x = 645 + (i * 20)
        pos_y = 24
        col = COLORE_VITA if i < vite_barca else (80, 80, 80)
        pygame.draw.circle(schermo, col, (pos_x, pos_y), 7)
        pygame.draw.circle(schermo, (255, 255, 255), (pos_x, pos_y), 7, 1)

    t_boost = font.render("Boost:", True, COLORE_TESTO)
    schermo.blit(t_boost, (735, 16))
    for i in range(pip_boost_massimi):
        pos_x = 795 + (i * 20)
        pos_y = 24
        col = COLORE_BOOST if i < pip_boost else (80, 80, 80)
        pygame.draw.circle(schermo, col, (pos_x, pos_y), 7)
        pygame.draw.circle(schermo, (255, 255, 255), (pos_x, pos_y), 7, 1)

    t_punti_hud = font.render(f"Punti: {punteggio_totale}", True, (255, 215, 0))
    schermo.blit(t_punti_hud, (875, 16))

    # --- BARRA INFERIORE (UI BOTTOM) ---
    barra_bottom = pygame.Surface((1000, 80), pygame.SRCALPHA)
    barra_bottom.fill((0, 0, 0, 190))
    schermo.blit(barra_bottom, (0, 620))

    t_lvl = font_grande.render(f"LIVELLO {livello_gioco}/30", True, (255, 215, 0))
    schermo.blit(t_lvl, (30, 645))

    colore_timer = (255, 50, 50) if tempo_rimanente_livello <= 5 else (255, 255, 255)
    t_timer = font_timer.render(f"00:{tempo_rimanente_livello:02d}", True, colore_timer)
    schermo.blit(t_timer, t_timer.get_rect(center=(500, 660)).topleft)

    centro_radar = (930, 660)
    raggio_radar = 28
    pygame.draw.circle(schermo, (10, 50, 120), centro_radar, raggio_radar)
    pygame.draw.circle(schermo, (255, 255, 255), centro_radar, raggio_radar, 2)

    rad_freccia = math.radians(angolo_vento)
    punta_x = centro_radar[0] + math.sin(rad_freccia) * (raggio_radar - 8)
    punta_y = centro_radar[1] - math.cos(rad_freccia) * (raggio_radar - 8)
    pygame.draw.line(schermo, (255, 255, 0), centro_radar, (punta_x, punta_y), 3)
    pygame.draw.circle(schermo, (255, 255, 255), centro_radar, 4)

    # Messaggi di Vittoria Livello / Vittoria Finale / Sconfitta
    if gioco_completato:
        sfon_fin = pygame.Surface((720, 150), pygame.SRCALPHA)
        sfon_fin.fill((0, 0, 0, 220))
        rect_sfon_fin = sfon_fin.get_rect(center=(500, 320))
        schermo.blit(sfon_fin, rect_sfon_fin.topleft)

        t_fin = font_grande.render("HAI COMPLETATO THE REAL PIRATE!", True, (255, 215, 0))
        t_punti_fin = font.render(f"Punteggio Totale Finale: {punteggio_totale} punti", True, (0, 220, 255))
        t_sub_fin = font.render("Premi [ENTER] per tornare al Title Screen", True, (255, 255, 255))

        schermo.blit(t_fin, t_fin.get_rect(center=(500, 280)).topleft)
        schermo.blit(t_punti_fin, t_punti_fin.get_rect(center=(500, 320)).topleft)
        schermo.blit(t_sub_fin, t_sub_fin.get_rect(center=(500, 360)).topleft)

    elif gioco_vinto:
        sfon_vittoria = pygame.Surface((700, 120), pygame.SRCALPHA)
        sfon_vittoria.fill((0, 0, 0, 210))
        rect_sfon = sfon_vittoria.get_rect(center=(500, 320))
        schermo.blit(sfon_vittoria, rect_sfon.topleft)

        t_vittoria = font_grande.render(f"LIVELLO {livello_gioco} SUPERATO!", True, (255, 215, 0))
        t_punti_parz = font.render(f"Punteggio Totale: {punteggio_totale}", True, (0, 220, 255))
        t_sub = font.render("Premi [ENTER] per passare al livello successivo", True, (255, 255, 255))
        
        schermo.blit(t_vittoria, t_vittoria.get_rect(center=(500, 290)).topleft)
        schermo.blit(t_punti_parz, t_punti_parz.get_rect(center=(500, 325)).topleft)
        schermo.blit(t_sub, t_sub.get_rect(center=(500, 355)).topleft)

    elif barca_distrutta:
        sfon_ko = pygame.Surface((600, 130), pygame.SRCALPHA)
        sfon_ko.fill((0, 0, 0, 210))
        rect_sfon_ko = sfon_ko.get_rect(center=(500, 320))
        schermo.blit(sfon_ko, rect_sfon_ko.topleft)

        if motivo_sconfitta == "tempo_scaduto":
            t_ko = font_grande.render("TEMPO SCADUTO!", True, (255, 120, 0))
        elif motivo_sconfitta == "avaria":
            t_ko = font_grande.render("BARCA IN AVARIA!", True, (255, 120, 0))
        else:
            t_ko = font_grande.render("BARCA ESPLOSA!", True, (255, 50, 50))

        t_punti_ko = font.render(f"Punteggio Finale Raggiunto: {punteggio_totale}", True, (0, 220, 255))
        t_sub_ko = font.render("Premi [ENTER] per ricominciare dal Livello 1", True, (255, 255, 255))

        schermo.blit(t_ko, t_ko.get_rect(center=(500, 280)).topleft)
        schermo.blit(t_punti_ko, t_punti_ko.get_rect(center=(500, 315)).topleft)
        schermo.blit(t_sub_ko, t_sub_ko.get_rect(center=(500, 350)).topleft)

    pygame.display.flip()
    orologio.tick(60)

pygame.quit()
sys.exit()
