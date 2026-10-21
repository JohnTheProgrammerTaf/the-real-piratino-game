"""THE PIRATINZ Arcade Edition.

Novità della versione 2.6.3:
  * Pip del boost fissato ad 1 per tutti i livelli.
  * Rimosso il sistema di accumulo vite extra tramite punteggio.
  * Frequenza dei fulmini velocizzata nei livelli tempestosi (28, 29, 30) per adattarsi ai tempi rapidi dei livelli.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
from array import array
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import lru_cache

import pygame

# ---------------------------------------------------------------------------
# COSTANTI
# ---------------------------------------------------------------------------
LARGHEZZA, ALTEZZA = 1000, 700
FPS = 60

USA_DELTA_TIME = True
EFFETTI_ATTIVI = True
MAX_PARTICELLE = 700

# Fisica dei barili
IMPULSO_ATTRITO = 0.93      # quanto in fretta si spegne una spinta ricevuta
RESTITUZIONE_BARILI = 0.8   # 1.0 = urto perfettamente elastico
RIMBALZO_OSTACOLI = 0.8     # rimbalzo contro isole e scogli

HUD_ALTO = 50            # altezza della barra superiore
HUD_BASSO_Y = 620        # y da cui parte la barra inferiore
BARCA_X_MIN, BARCA_X_MAX = 20, 980
BARCA_Y_MIN, BARCA_Y_MAX = 60, 600
RAGGIO_BARCA = 15        # usato nelle collisioni con i barili
RAGGIO_PORTO_B = 55

ACCELERAZIONE = 0.05
ATTRITO = 0.985
VELOCITA_ANGOLARE = 3    # gradi per frame (a 60 FPS)
DURATA_INVULNERABILITA = 1000   # ms dopo un danno
DURATA_BOOST = 1000             # ms
LIVELLO_FINALE = 30

FULMINE_MIN_MS = 3000
FULMINE_MAX_MS = 7000
FULMINE_NEXT_MIN_MS = 4000
FULMINE_NEXT_MAX_MS = 9000

SCALA_ESPLOSIONE_GRANDE = 1.7

# Leaderboard
POSTI_CLASSIFICA = 10
FILE_CLASSIFICA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "classifica_real_pirate.json"
)
ATTESA_CLASSIFICA_MS = 10_000      # inattività sul Title prima di mostrare la classifica
DURATA_CLASSIFICA_AUTO_MS = 12_000 # quanto resta a schermo quando compare da sola
LUNGHEZZA_NICK = 3

SECONDI_LIVELLO = 15               # timer uguale in tutti i livelli
LIVELLO_BARILI_ROSSI = 28          # da questo livello in poi tutti i barili sono esplosivi
LIVELLO_OST_EPICA = 28             # da questo livello in poi suona l'OST epica
DURATA_TRANSIZIONE_MS = 900        # schermata comandi -> gioco (spinta del vento)
DURATA_LAMPEGGIO_MS = 1000         # minimo di lampeggio della barca al livello 1
RITARDO_RECORD_MS = 900            # pausa dopo il Game Over prima dell'annuncio record
DURATA_RECORD_MS = 3600            # durata dell'annuncio (la fanfara dura ~3,4 s)
SKIP_RECORD_DOPO_MS = 1500         # da quando si può saltare l'annuncio con un tasto
SCALA_VELA = 0.65                  # dimensione della vela (1.0 = originale, 0.65 = -35%)
PIXEL_MARE = 8                     # lato di un "pixel" del mare stilizzato
ALTEZZA_MARE_PIXEL = 56            # il mare occupa 56 px in basso (8% dello schermo)

VENTI = [
    ("NORD", 0), ("NORD-EST", 45), ("EST", 90), ("SUD-EST", 135),
    ("SUD", 180), ("SUD-OVEST", 225), ("OVEST", 270), ("NORD-OVEST", 315),
]

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
COLORE_ORO = (255, 215, 0)
COLORE_SPENTO = (80, 80, 80)
SCHIUMA = (235, 245, 255)
ACQUA_CHIARA = (140, 215, 255)
FUOCO = [(255, 215, 0), (255, 140, 0), (255, 69, 0)]
FUMO = (70, 70, 70)
LEGNO = (139, 69, 19)


# ---------------------------------------------------------------------------
# CONFIGURAZIONE DEI LIVELLI E ATMOSFERE
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ConfigLivello:
    pip_boost: int
    secondi: int
    forza_max: int
    moltiplicatore: float
    n_isole: int
    n_scogli: int
    n_barili: int


@dataclass(frozen=True)
class AtmosferaLivello:
    tinta_mare: tuple[int, int, int, int] | None
    nuvole: bool
    pioggia: bool
    fulmini: bool


def atmosfera_livello(numero: int) -> AtmosferaLivello:
    if numero <= 10:
        return AtmosferaLivello(tinta_mare=None, nuvole=False, pioggia=False, fulmini=False)
    elif numero <= 20:
        return AtmosferaLivello(tinta_mare=(220, 90, 30, 45), nuvole=True, pioggia=False, fulmini=False)
    elif numero <= 27:
        return AtmosferaLivello(tinta_mare=(20, 30, 55, 75), nuvole=True, pioggia=True, fulmini=False)
    else:
        return AtmosferaLivello(tinta_mare=(10, 15, 35, 105), nuvole=True, pioggia=True, fulmini=True)


def moltiplicatore_livello(numero: int) -> float:
    if numero <= 10:
        return 1.5
    if numero <= 20:
        return 2.0
    if numero <= 27:
        return 2.5
    return 3.0


def config_livello(numero: int) -> ConfigLivello:
    fascia = 0 if numero < 10 else (1 if numero < 20 else 2)
    return ConfigLivello(
        pip_boost=1,  # Fisso ad 1 per tutti i livelli
        secondi=SECONDI_LIVELLO,
        forza_max=(4, 5, 6)[fascia],
        moltiplicatore=moltiplicatore_livello(numero),
        n_isole=min(8, 3 + max(0, numero - 1) // 2),
        n_scogli=min(14, 4 + max(0, numero - 1) // 2),
        n_barili=min(12, 6 + numero // 3),
    )


# ---------------------------------------------------------------------------
# AUDIO E GENERAZIONE PROCEDURALE MODULARE
# ---------------------------------------------------------------------------
SAMPLE_RATE = 22050

RIPOSO = 0
G3, A3, B3 = 196.00, 220.00, 246.94
C4, D4, E4, F4, G4, A4, B4 = (
    261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88
)
C5, D5, E5, F5 = 523.25, 587.33, 659.25, 698.46
G5, A5, B5 = 783.99, 880.00, 987.77
C6, D6 = 1046.50, 1174.66

MELODIA_TITLE = (
    [(A5, 0.45), (A5, 0.40), (A5, 0.25), (A5, 0.35), (A5, 0.35), (A5, 0.30), (A5, 0.35), (D5, 0.60), (F5, 0.50), (A5, 0.60)] +
    [(G5, 0.45), (G5, 0.40), (G5, 0.25), (G5, 0.35), (G5, 0.35), (G5, 0.30), (G5, 0.35), (C5, 0.60), (E5, 0.50), (G5, 0.60)] +
    [(A5, 0.45), (A5, 0.40), (A5, 0.25), (A5, 0.35), (A5, 0.35), (A5, 0.30), (A5, 0.35), (B5, 0.60), (C6, 0.50), (D6, 0.60)] +
    [(C6, 0.45), (A5, 0.45), (G5, 0.45), (E5, 0.50), (D5, 0.75), (D5, 0.95)]
)

BASE_MELODIA_PRINCIPALE = (
    [(D4, .25)] * 5 + [(F4, .25), (A4, .50), (D4, .50), (RIPOSO, .20)]
    + [(C4, .25)] * 4 + [(E4, .25), (G4, .25), (E4, .50), (C4, .50), (RIPOSO, .20)]
    + [(D4, .25), (F4, .25), (A4, .25), (C5, .50), (A4, .25), (G4, .25),
       (F4, .50), (D4, 1.20), (RIPOSO, 1.00)]
)

MELODIA_FANFARA = [
    ([G4], .13), ([G4], .13), ([G4], .13), ([C5], .50),
    ([A4], .13), ([A4], .13), ([A4], .13), ([D5], .50),
    ([E5], .16), ([D5], .16), ([E5], .16), ([C5, E5, G5], 1.10),
]
ARMONICHE_OTTONI = ((1, 1.0), (2, 0.6), (3, 0.4), (4, 0.25))

PASSO_EPICO = 0.20
Bb4, Ab4, Eb4, Cs5, F5 = 466.16, 415.30, 311.13, 554.37, 698.46
D2, Bb1, Eb2, A1, G2 = 73.42, 58.27, 77.78, 55.00, 98.00
MELODIA_EPICA = (
    [(D4, 1)] * 5 + [(F4, 1), (A4, 2)],
    [(D5, 2), (C5, 1), (Bb4, 1), (A4, 2), (F4, 2)],
    [(D4, 1)] * 5 + [(Eb4, 1), (Ab4, 2)],
    [(Bb4, 2), (A4, 2), (G4, 1), (F4, 1), (E4, 2)],
    [(A4, 1)] * 5 + [(C5, 1), (E5, 2)],
    [(F5, 2), (E5, 1), (D5, 1), (C5, 2), (A4, 2)],
)
RADICI_EPICHE = (D2, Bb1, Eb2, A1, G2, Bb1, Eb2, A1)
GALOPPO = (1, 1, 2, 1, 1, 2, 1, 2)


def _ost_modulare(livello: int) -> list[int]:
    sr, tau = SAMPLE_RATE, 2 * math.pi
    campioni_base = _melodia(BASE_MELODIA_PRINCIPALE, 3000, 0.6, attacco=800, fade_finale=1.5)
    totale = len(campioni_base)
    master = [float(v) for v in campioni_base]

    def mix(altra_traccia: list[float], guadagno: float = 1.0) -> None:
        for i, val in enumerate(altra_traccia):
            if i < totale:
                master[i] += val * guadagno

    rnd = random.Random(livello + 42)

    if livello >= 1:
        tamburo = [0.0] * totale
        for i in range(0, totale, int(sr * 0.5)):
            for k in range(int(sr * 0.1)):
                if i + k < totale:
                    t = k / sr
                    tamburo[i + k] += rnd.uniform(-1, 1) * 1500 * math.exp(-t * 20)
        mix(tamburo, 0.6)

    if livello >= 11:
        violino = []
        for i in range(totale):
            t = i / sr
            vibrato = math.sin(tau * 6 * t) * 3
            freq = 440.0 + vibrato
            saw = 2000 * (2 * ((freq * t) % 1.0) - 1)
            violino.append(saw * 0.4 * min(1.0, i / (sr * 0.2)))
        mix(violino, 0.5)

        cori = []
        for i in range(totale):
            t = i / sr
            v = 1500 * (math.sin(tau * 220 * t) + 0.5 * math.sin(tau * 440 * t)) * 0.3
            cori.append(v * min(1.0, i / (sr * 0.4)))
        mix(cori, 0.7)

    if livello >= 21:
        ottoni = []
        for i in range(totale):
            t = i / sr
            brass_v = sum(peso * math.sin(tau * 293.66 * h * t) for h, peso in ARMONICHE_OTTONI)
            ottoni.append(2500 * brass_v * 0.4)
        mix(ottoni, 0.8)

        rullante_pesante = [0.0] * totale
        for i in range(int(sr * 0.25), totale, int(sr * 0.5)):
            for k in range(int(sr * 0.15)):
                if i + k < totale:
                    t = k / sr
                    rullante_pesante[i + k] += rnd.uniform(-1, 1) * 3500 * math.exp(-t * 15)
        mix(rullante_pesante, 1.0)

    return [int(20000 * math.tanh(0.75 * v / 20000)) for v in master]


def _ost_epica() -> list[int]:
    sr, tau = SAMPLE_RATE, 2 * math.pi
    passo = int(sr * PASSO_EPICO)
    n_passi = 8 * 8
    master = [0.0] * (passo * n_passi)
    rnd = random.Random(3)
    totale = len(master)

    def mescola(inizio: int, campioni: list[float]) -> None:
        for j, v in enumerate(campioni):
            master[(inizio + j) % totale] += v

    @lru_cache(maxsize=None)
    def lead(freq: float, passi: int) -> list[float]:
        n = int(passo * passi * 0.92)
        att, rel = int(sr * 0.012), int(sr * 0.05)
        w = tau * freq / sr
        out = []
        for i in range(n):
            ph = w * i
            if passi >= 2:
                ph += 0.5 * (i / n) * math.sin(tau * 5.5 * i / sr)
            v = math.sin(ph) + 0.6 * math.sin(2 * ph) + 0.35 * math.sin(3 * ph)
            out.append(3200 * v * min(1.0, i / att, (n - i) / rel))
        return out

    @lru_cache(maxsize=None)
    def basso(freq: float) -> list[float]:
        n = int(passo * 0.85)
        att, rel = int(sr * 0.004), int(sr * 0.06)
        out = []
        for i in range(n):
            t = i / sr
            dente = 2 * ((freq * t) % 1.0) - 1
            v = 0.55 * math.sin(tau * freq * t) + 0.45 * dente
            out.append(4200 * v * min(1.0, i / att, (n - i) / rel))
        return out

    @lru_cache(maxsize=None)
    def pad(radice: float) -> list[float]:
        n = passo * 8
        att, rel = int(sr * 0.5), int(sr * 0.4)
        out = []
        for i in range(n):
            t = i / sr
            tremolo = 0.75 + 0.25 * math.sin(tau * 6 * t)
            v = (math.sin(tau * radice * 4 * t) + 0.8 * math.sin(tau * radice * 6 * t)) * tremolo
            out.append(850 * v * min(1.0, i / att, (n - i) / rel))
        return out

    n_k = int(sr * 0.22)
    fase, grancassa = 0.0, []
    for i in range(n_k):
        t = i / sr
        fase += tau * (45 + 90 * math.exp(-t * 25)) / sr
        grancassa.append(6000 * math.sin(fase) * math.exp(-t * 14))
    rullante = [
        (4000 * rnd.uniform(-1, 1) * math.exp(-i / sr * 22)
         + 2000 * math.sin(tau * 190 * i / sr) * math.exp(-i / sr * 30))
        for i in range(int(sr * 0.18))
    ]
    rumore = [rnd.uniform(-1, 1) for _ in range(int(sr * 0.05) + 1)]
    hihat = [1400 * (rumore[i + 1] - rumore[i]) * math.exp(-i / sr * 70)
             for i in range(len(rumore) - 1)]

    pos = 0
    for battuta in MELODIA_EPICA:
        for freq, passi in battuta:
            mescola(pos * passo, lead(freq, passi))
            pos += passi

    for b, radice in enumerate(RADICI_EPICHE):
        mescola(b * 8 * passo, pad(radice))
        riempimento = b in (3, 7)
        for s, ottava in enumerate(GALOPPO):
            p = (b * 8 + s) * passo
            mescola(p, basso(radice * ottava))
            mescola(p, hihat)
            if s in (0, 4):
                mescola(p, grancassa)
            if not riempimento and s in (2, 6):
                mescola(p, rullante)
            if riempimento and s >= 4:
                mescola(p, rullante)
                if s >= 6:
                    mescola(p + passo // 2, rullante)

    return [int(20000 * math.tanh(0.75 * v / 20000)) for v in master]


GAIN_GH = 0.3


def _aaargh() -> list[int]:
    sr, tau = SAMPLE_RATE, 2 * math.pi
    rnd = random.Random(7)
    n = int(sr * 1.3)
    chiavi = [
        (0.00, 100, 450, 1000, 2400, 0.0, 0.0, 0.05),
        (0.06, 125, 650, 1100, 2500, 1.0, 0.0, 0.05),
        (0.20, 150, 780, 1150, 2600, 1.0, 0.0, 0.05),
        (0.55, 155, 760, 1150, 2600, 1.0, 0.1, 0.08),
        (0.68, 135, 520, 1250, 1750, 0.95, 0.6, 0.15),
        (1.00, 95, 480, 1300, 1650, 0.85, 0.8, 0.20),
        (1.10, 85, 350, 1100, 1900, 0.45, 0.3, 0.35),
        (1.30, 80, 300, 1200, 2200, 0.0, 0.0, 0.45),
    ]

    def parametri(t: float) -> list[float]:
        for a, b in zip(chiavi, chiavi[1:]):
            if a[0] <= t <= b[0]:
                k = (t - a[0]) / (b[0] - a[0])
                return [x + (y - x) * k for x, y in zip(a[1:], b[1:])]
        return list(chiavi[-1][1:])

    pesi, qualita = (1.0, 0.7, 0.45), (9.0, 11.0, 13.0)
    stati = [[0.0, 0.0, 0.0, 0.0] for _ in range(3)]
    coeff: list[tuple[float, float, float]] = []
    f0 = ampiezza = ringhio = soffio = 0.0
    fase = 0.0
    w0 = tau * 2200 / sr
    alfa = math.sin(w0) / 2.0
    n_b0, n_a1, n_a2 = alfa / (1 + alfa), -2 * math.cos(w0) / (1 + alfa), (1 - alfa) / (1 + alfa)
    sx1 = sx2 = sy1 = sy2 = 0.0
    out: list[float] = []
    for i in range(n):
        t = i / sr
        if i % 32 == 0:
            f0, f1, f2, f3, ampiezza, ringhio, soffio = parametri(t)
            f0 *= (1 + 0.03 * math.sin(tau * 5.5 * t)) * (1 + 0.02 * (rnd.random() - 0.5))
            coeff = []
            for freq, q in zip((f1, f2, f3), qualita):
                w0 = tau * freq / sr
                alfa = math.sin(w0) / (2 * q)
                a0 = 1 + alfa
                coeff.append((alfa / a0, -2 * math.cos(w0) / a0, (1 - alfa) / a0))
        fase += f0 / sr
        r = rnd.uniform(-1, 1)
        sorgente = (2 * (fase % 1.0) - 1) + soffio * r
        sorgente *= ampiezza * (1 - ringhio * (0.5 + 0.5 * math.sin(tau * 32 * t)) ** 2)
        y = 0.0
        for k in range(3):
            b0, a1, a2 = coeff[k]
            x1, x2, y1, y2 = stati[k]
            yk = b0 * (sorgente - x2) - a1 * y1 - a2 * y2
            stati[k] = [sorgente, x1, yk, y1]
            y += pesi[k] * yk
        gh = max(0.0, 1 - abs(t - 1.13) / 0.12)
        ys = n_b0 * (r - sx2) - n_a1 * sy1 - n_a2 * sy2
        sx2, sx1, sy2, sy1 = sx1, r, sy1, ys
        y += gh * gh * ys * GAIN_GH
        out.append(y)
    rms = math.sqrt(sum(v * v for v in out) / len(out)) or 1.0
    scala = 4200 / rms
    return [max(-30000, min(30000, int(v * scala))) for v in out]


def _tuono_sintetizzato() -> list[int]:
    sr = SAMPLE_RATE
    rnd = random.Random()
    n = int(sr * 1.2)
    out = []
    fase = 0.0
    for i in range(n):
        t = i / sr
        env = math.exp(-t * 3.5) * min(1.0, t * 20.0)
        rumore = rnd.uniform(-1, 1)
        fase += (60 + 40 * math.sin(t * 8)) / sr
        basso = math.sin(2 * math.pi * fase)
        v = (rumore * 0.6 + basso * 0.4) * env * 22000
        out.append(int(v))
    return out


def _a_suono(campioni: list[int]) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(buffer=array("h", campioni).tobytes())


def _effetto(durata: float, onda) -> list[int]:
    n = int(SAMPLE_RATE * durata)
    return [int(onda(i, i / SAMPLE_RATE) * (1 - i / n)) for i in range(n)]


def _melodia(note, ampiezza, esponente, attacco=0, fade_finale=0.0) -> list[int]:
    campioni: list[int] = []
    for freq, durata in note:
        n = int(SAMPLE_RATE * durata)
        if freq == RIPOSO:
            campioni.extend([0] * n)
            continue
        w = 2 * math.pi * freq / SAMPLE_RATE
        campioni.extend(
            int(ampiezza * math.sin(w * i) * (1 - (i / n) ** esponente))
            for i in range(n)
        )
    for i in range(min(attacco, len(campioni))):
        campioni[i] = int(campioni[i] * i / attacco)
    if fade_finale:
        fade = int(SAMPLE_RATE * fade_finale)
        tot = len(campioni)
        for k in range(max(0, tot - fade), tot):
            campioni[k] = int(campioni[k] * (tot - k) / fade)
    return campioni


def _fanfara(note, ampiezza: float = 4500) -> list[int]:
    campioni: list[int] = []
    for freqs, durata in note:
        n = int(SAMPLE_RATE * durata)
        attacco = max(1, int(n * 0.06))
        rilascio = max(1, int(n * 0.25))
        scala = ampiezza / math.sqrt(len(freqs))
        for i in range(n):
            t = i / SAMPLE_RATE
            v = sum(peso * math.sin(2 * math.pi * f * h * t)
                    for f in freqs for h, peso in ARMONICHE_OTTONI)
            inviluppo = min(1.0, i / attacco, (n - i) / rilascio)
            campioni.append(int(scala * v * inviluppo))
    return campioni


class Audio:
    def __init__(self) -> None:
        self.attivo = False
        self.suoni: dict[str, pygame.mixer.Sound] = {}
        self.ost_title = None
        self.ost_livello = None
        self.ost_epica = None

        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            self.attivo = pygame.mixer.get_init() is not None
        except pygame.error as errore:
            print("ATTENZIONE: audio non disponibile, si gioca senza suoni:", errore)

        if self.attivo:
            print("Audio inizializzato con successo:", pygame.mixer.get_init())
            self._genera()

    def _genera(self) -> None:
        tau = 2 * math.pi
        vittoria: list[int] = []
        for nota in (523.25, 659.25, 783.99):
            vittoria += _effetto(
                0.4 / 3, lambda i, t, nota=nota: 8000 * math.sin(tau * nota * t)
            )
        self.suoni = {
            "boost": _a_suono(_effetto(
                0.25, lambda i, t: 16383 * math.sin(tau * (300 + i * 4) * t))),
            "danno": _a_suono(_effetto(
                0.15, lambda i, t: 20000 * math.sin(tau * 120 * t))),
            "esplosione": _a_suono(_effetto(
                0.40, lambda i, t: random.uniform(-16383, 16383))),
            "gameover": _a_suono(_effetto(
                0.50, lambda i, t: 20000 * math.sin(tau * max(50, 300 - i * 0.5) * t))),
            "vittoria": _a_suono(vittoria),
            "fanfara": _a_suono(_fanfara(MELODIA_FANFARA)),
            "aaargh": _a_suono(_aaargh()),
            "moneta": _a_suono(_effetto(
                0.15, lambda i, t: 15000 * math.sin(tau * (900 + i * 8) * t))),
            "tic": _a_suono(_effetto(
                0.05, lambda i, t: 8000 * math.sin(tau * 1200 * t))),
            "tuono": _a_suono(_tuono_sintetizzato()),
            "vita_extra": _a_suono(_effetto(
                0.30, lambda i, t: 18000 * math.sin(tau * (400 + i * 10) * t))),
        }
        self.ost_title = _a_suono(_melodia(MELODIA_TITLE, 4000, 0.5))
        self.ost_epica = _a_suono(_ost_epica())

    def play(self, nome: str) -> None:
        if self.attivo and nome in self.suoni:
            self.suoni[nome].play()

    def avvia_title(self) -> None:
        if self.attivo:
            self.ost_title.play(loops=-1)

    def ferma_title(self) -> None:
        if self.attivo:
            self.ost_title.stop()

    def avvia_ost_livello(self, numero_livello: int, epica: bool = False) -> None:
        if not self.attivo:
            return
        self.ferma_ost_livello()
        if epica:
            self.ost_livello = self.ost_epica
        else:
            dati = _ost_modulare(numero_livello)
            self.ost_livello = _a_suono(dati)
        self.ost_livello.play(loops=-1)

    def ferma_ost_livello(self) -> None:
        if self.attivo and self.ost_livello:
            self.ost_livello.stop()

    def pausa(self) -> None:
        if self.attivo:
            pygame.mixer.pause()

    def riprendi(self) -> None:
        if self.attivo:
            pygame.mixer.unpause()


# ---------------------------------------------------------------------------
# ENTITÀ
# ---------------------------------------------------------------------------
class Schermata(Enum):
    TITLE = auto()
    ISTRUZIONI = auto()
    GIOCO = auto()
    CLASSIFICA = auto()


class Esito(Enum):
    IN_CORSO = auto()
    SUPERATO = auto()
    COMPLETATO = auto()
    DISTRUTTA = auto()


@dataclass
class Cerchio:
    x: int
    y: int
    raggio: int
    fase: float = field(default_factory=random.random)

    @property
    def pos(self) -> tuple[int, int]:
        return self.x, self.y


@dataclass(eq=False)
class Barile:
    x: float
    y: float
    velocita_extra: float
    fase: float
    rosso: bool
    raggio: int = 16
    ix: float = 0.0
    iy: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    pausa_fx: float = 0.0

    @classmethod
    def casuale(cls, x: float, y: float, vmax: float,
                rosso: bool | None = None) -> "Barile":
        return cls(
            x=x, y=y,
            velocita_extra=random.uniform(0.7, vmax),
            fase=random.uniform(0, 6.28),
            rosso=(random.random() < 0.28) if rosso is None else rosso,
        )


class Vento:
    def __init__(self, forza_max: int, now: int) -> None:
        self.nome, self.angolo = random.choice(VENTI)
        self._sorteggia(forza_max, now)

    def _sorteggia(self, forza_max: int, now: int) -> None:
        self.forza = random.randint(1, forza_max)
        self.ultimo_cambio = now
        self.intervallo = random.randint(2, 5) * 1000

    def scaduto(self, now: int) -> bool:
        return now - self.ultimo_cambio > self.intervallo

    def cambia(self, forza_max: int, now: int) -> None:
        self.nome, self.angolo = random.choice(
            [v for v in VENTI if v[0] != self.nome]
        )
        self._sorteggia(forza_max, now)

    def secondi_al_cambio(self, now: int) -> int:
        return max(0, int((self.intervallo - (now - self.ultimo_cambio)) / 1000))


class Barca:
    __slots__ = (
        "x", "y", "angolo", "velocita", "angolo_vela", "vite", "ultimo_danno"
    )

    def __init__(self, x: float, y: float, angolo_vela: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.angolo = 0.0
        self.velocita = 0.0
        self.angolo_vela = angolo_vela
        self.vite = 3
        self.ultimo_danno = -DURATA_INVULNERABILITA - 1

    def avanza(self, angolo_deg: float, distanza: float) -> None:
        rad = math.radians(angolo_deg)
        self.x += distanza * math.sin(rad)
        self.y -= distanza * math.cos(rad)

    def vela_verso(self, angolo_vento: float, f: float) -> None:
        diff = (angolo_vento - self.angolo_vela + 180) % 360 - 180
        self.angolo_vela += diff * (1 - 0.95 ** f)

    def respingi_da(self, cx: float, cy: float, raggio: float) -> None:
        ang = math.atan2(self.y - cy, self.x - cx)
        self.x = cx + math.cos(ang) * raggio
        self.y = cy + math.sin(ang) * raggio

    def puo_subire_danno(self, now: int) -> bool:
        return now - self.ultimo_danno > DURATA_INVULNERABILITA

    def in_invulnerabilita(self, now: int) -> bool:
        return now - self.ultimo_danno < DURATA_INVULNERABILITA

    def limita_allo_schermo(self) -> None:
        self.x = max(BARCA_X_MIN, min(self.x, BARCA_X_MAX))
        self.y = max(BARCA_Y_MIN, min(self.y, BARCA_Y_MAX))


# ---------------------------------------------------------------------------
# EFFETTI (particelle)
# ---------------------------------------------------------------------------
class Particella:
    __slots__ = ("x", "y", "vx", "vy", "vita", "vita_max", "r0", "r1",
                 "colore", "alpha0", "drag", "larghezza", "strato")

    def __init__(self, x, y, vx, vy, vita, r0, r1, colore, alpha0,
                 drag=0.95, larghezza=0, strato=1):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.vita = self.vita_max = vita
        self.r0, self.r1 = r0, r1
        self.colore, self.alpha0 = colore, alpha0
        self.drag, self.larghezza, self.strato = drag, larghezza, strato


class Effetti:
    def __init__(self) -> None:
        self.particelle: list[Particella] = []

    def _nuova(self, *args, **kwargs) -> None:
        if EFFETTI_ATTIVI and len(self.particelle) < MAX_PARTICELLE:
            self.particelle.append(Particella(*args, **kwargs))

    def contiene(self, strato: int) -> bool:
        return any(p.strato == strato for p in self.particelle)

    def aggiorna(self, f: float) -> None:
        if not self.particelle:
            return
        vive = []
        for p in self.particelle:
            p.vita -= f
            if p.vita <= 0:
                continue
            p.x += p.vx * f
            p.y += p.vy * f
            d = p.drag ** f
            p.vx *= d
            p.vy *= d
            vive.append(p)
        self.particelle = vive

    def disegna(self, superficie, strato: int) -> None:
        for p in self.particelle:
            if p.strato != strato:
                continue
            u = 1 - p.vita / p.vita_max
            alpha = int(p.alpha0 * (1 - u))
            if alpha <= 0:
                continue
            raggio = max(1, int(p.r0 + (p.r1 - p.r0) * u))
            pygame.draw.circle(superficie, (*p.colore, alpha),
                               (int(p.x), int(p.y)), raggio, p.larghezza)

    def schiuma_scia(self, x, y, px, py, boost) -> None:
        colore = COLORE_BOOST if boost else SCHIUMA
        lat = 0.45 if boost else 0.30
        for lato in (-1, 1):
            self._nuova(x + lato * px * 5, y + lato * py * 5,
                        lato * px * lat + random.uniform(-.06, .06),
                        lato * py * lat + random.uniform(-.06, .06),
                        random.uniform(34, 46), 3, 9 if boost else 7,
                        colore, 190 if boost else 150, 0.95, strato=0)
        self._nuova(x, y, 0, 0, random.uniform(20, 28), 4 if boost else 3, 2,
                    colore, 120, 0.9, strato=0)

    def scia_barile(self, x, y) -> None:
        self._nuova(x, y, random.uniform(-.1, .1), random.uniform(-.1, .1),
                    random.uniform(20, 30), 2, 5, SCHIUMA, 110, 0.95, strato=0)

    def anello(self, x, y, r0, r1, colore, alpha0, vita, larghezza, strato=1) -> None:
        self._nuova(x, y, 0, 0, vita, r0, r1, colore, alpha0, 1.0,
                    larghezza=larghezza, strato=strato)

    def schizzo(self, x, y, n, vmax) -> None:
        self.anello(x, y, 4, 24, SCHIUMA, 140, 18, 2, strato=0)
        for _ in range(n):
            ang = random.uniform(0, 2 * math.pi)
            vel = random.uniform(0.6, vmax)
            self._nuova(x, y, math.cos(ang) * vel, math.sin(ang) * vel,
                        random.uniform(14, 24), 2.5, 1,
                        random.choice((SCHIUMA, ACQUA_CHIARA)), 210, 0.90)

    def spruzzo(self, x, y, vx, vy) -> None:
        self._nuova(x, y, vx, vy, random.uniform(16, 24), 2.5, 4, SCHIUMA, 150, 0.94)

    def esplosione(self, x, y, grande=False) -> None:
        s = SCALA_ESPLOSIONE_GRANDE if grande else 1.0
        self.anello(x, y, 8 * s, 70 * s, (255, 200, 120), 200, 22, 3)
        for _ in range(int(10 * s)):
            ang, vel = random.uniform(0, 2 * math.pi), random.uniform(0.3, 1.2) * s
            self._nuova(x, y, math.cos(ang) * vel, math.sin(ang) * vel,
                        random.uniform(50, 70), 6 * s, 16 * s, FUMO, 170, 0.97)
        for _ in range(int(22 * s)):
            ang, vel = random.uniform(0, 2 * math.pi), random.uniform(0.8, 3.8) * s
            self._nuova(x, y, math.cos(ang) * vel, math.sin(ang) * vel,
                        random.uniform(18, 34), random.uniform(4, 8) * s,
                        random.uniform(9, 15) * s, random.choice(FUOCO), 230, 0.93)
        self.detriti(x, y, int(8 * s))
        self.schizzo(x, y, int(10 * s), 3.0 * s)

    def detriti(self, x, y, n) -> None:
        for _ in range(n):
            ang, vel = random.uniform(0, 2 * math.pi), random.uniform(1.5, 4.0)
            self._nuova(x, y, math.cos(ang) * vel, math.sin(ang) * vel,
                        random.uniform(30, 45), 3, 1.5, LEGNO, 255, 0.95)

    def scintille(self, x, y) -> None:
        for _ in range(36):
            ang, vel = random.uniform(0, 2 * math.pi), random.uniform(1.0, 4.0)
            self._nuova(x, y, math.cos(ang) * vel, math.sin(ang) * vel,
                        random.uniform(30, 50), 3, 0.5,
                        random.choice((COLORE_ORO, SCHIUMA)), 240, 0.94)

    def getto_boost(self, x, y) -> None:
        self.anello(x, y, 12, 55, COLORE_BOOST, 200, 20, 3)
        for _ in range(14):
            ang, vel = random.uniform(0, 2 * math.pi), random.uniform(1.0, 3.0)
            self._nuova(x, y, math.cos(ang) * vel, math.sin(ang) * vel,
                        random.uniform(14, 22), 3, 1, COLORE_BOOST, 220, 0.92)


# ---------------------------------------------------------------------------
# LIVELLO (mondo + meteo + fisica)
# ---------------------------------------------------------------------------
class Livello:
    def __init__(self, numero: int, now: int, audio: Audio) -> None:
        self.numero = numero
        self.cfg = config_livello(numero)
        self.atmosfera = atmosfera_livello(numero)
        self.audio = audio

        self.porto_a = (random.randint(80, 250), random.randint(150, 550))
        self.porto_b = (random.randint(750, 920), random.randint(150, 550))
        self.vento = Vento(self.cfg.forza_max, now)
        self.barca = Barca(*self.porto_a, angolo_vela=float(self.vento.angolo))

        self.isole = self._genera_isole()
        self.scogli = self._genera_scogli()
        self.barili = self._genera_barili()

        self.monete = self._genera_monete()
        self.monete_totali_livello = len(self.monete)
        self.monete_raccolte_livello = 0
        self.punti_monete = 0
        self.testi_fluttuanti = []

        self.nuvole = self._genera_nuvole() if self.atmosfera.nuvole else []
        self.gocce_pioggia = [
            {"x": random.randint(0, LARGHEZZA), "y": random.randint(0, ALTEZZA), "vel": random.uniform(12, 18)}
            for _ in range(50)
        ] if self.atmosfera.pioggia else []

        self.flash_fulmine_timer = 0
        # Frequenza velocizzata all'avvio nei livelli dal 28 in poi
        if self.atmosfera.fulmini:
            min_ms = 1000 if numero >= 28 else FULMINE_MIN_MS
            max_ms = 3000 if numero >= 28 else FULMINE_MAX_MS
            self.prossimo_fulmine = now + random.randint(min_ms, max_ms)
        else:
            self.prossimo_fulmine = 0

        self.pip_boost = self.cfg.pip_boost
        self.tempo_fine_boost = 0
        self.timer_avviato = False
        self.tempo_inizio = 0
        self.secondi_rimanenti = self.cfg.secondi
        self.lampeggio_fino = now + DURATA_LAMPEGGIO_MS if numero == 1 else 0

        self.esito = Esito.IN_CORSO
        self.motivo = ""
        self.punti = 0
        self.stato_vela = ""
        self.danni_subiti = 0
        self.fx = Effetti()
        self._acc_scia = 0.0

    def _genera_nuvole(self) -> list[dict]:
        nuvole = []
        for _ in range(5):
            rx, ry = random.randint(100, 180), random.randint(40, 70)
            surf = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (10, 20, 40, 45), (0, 0, rx * 2, ry * 2))
            nuvole.append({
                "x": random.randint(0, LARGHEZZA),
                "y": random.randint(HUD_ALTO + 20, HUD_BASSO_Y - 20),
                "rx": rx, "ry": ry,
                "surf": surf
            })
        return nuvole

    def _aggiungi_testo_fluttuante(self, x: float, y: float, testo: str, colore: tuple) -> None:
        self.testi_fluttuanti.append({
            "x": x,
            "y": y,
            "testo": testo,
            "colore": colore,
            "vita": 45
        })

    def _lontano_dai_porti(self, x: float, y: float, distanza: float) -> bool:
        return (math.hypot(x - self.porto_a[0], y - self.porto_a[1]) > distanza
                and math.hypot(x - self.porto_b[0], y - self.porto_b[1]) > distanza)

    def _genera_isole(self) -> list[Cerchio]:
        isole: list[Cerchio] = []
        for _ in range(self.cfg.n_isole):
            for _tentativo in range(100):
                x, y = random.randint(280, 720), random.randint(130, 570)
                libero = all(
                    math.hypot(x - i.x, y - i.y) >= i.raggio + 45 for i in isole
                )
                if libero and self._lontano_dai_porti(x, y, 130):
                    isole.append(Cerchio(x, y, random.randint(30, 50)))
                    break
        return isole

    def _genera_scogli(self) -> list[Cerchio]:
        scogli: list[Cerchio] = []
        for _ in range(self.cfg.n_scogli):
            for _tentativo in range(100):
                x, y = random.randint(150, 850), random.randint(100, 600)
                libero = (
                    all(math.hypot(x - i.x, y - i.y) >= i.raggio + 25 for i in self.isole)
                    and all(math.hypot(x - s.x, y - s.y) >= 35 for s in scogli)
                )
                if libero and self._lontano_dai_porti(x, y, 90):
                    scogli.append(Cerchio(x, y, random.randint(14, 24)))
                    break
        return scogli

    def _genera_barili(self) -> list[Barile]:
        barili: list[Barile] = []
        for _ in range(self.cfg.n_barili):
            while True:
                x = random.randint(50, 950)
                y = random.randint(BARCA_Y_MIN, BARCA_Y_MAX)
                if self._lontano_dai_porti(x, y, 80):
                    barili.append(Barile.casuale(
                        x, y, 1.5, rosso=True if self.numero >= LIVELLO_BARILI_ROSSI else None))
                    break
        return barili

    def _genera_monete(self) -> list[dict]:
        monete = []
        raggio = 8
        num_monete = random.randint(3, 6)
        for _ in range(num_monete):
            for _tentativo in range(100):
                x = random.randint(100, 900)
                y = random.randint(HUD_ALTO + 30, HUD_BASSO_Y - 30)
                libera = (
                    self._lontano_dai_porti(x, y, 90)
                    and all(math.hypot(x - o.x, y - o.y) >= o.raggio + raggio + RAGGIO_BARCA
                            for o in self.isole + self.scogli)
                    and all(math.hypot(x - m["x"], y - m["y"]) >= 2 * raggio + 10
                            for m in monete)
                )
                if libera:
                    monete.append({"x": x, "y": y, "raggio": raggio})
                    break
        return monete

    def in_lampeggio_iniziale(self, now: int) -> bool:
        return (self.numero == 1 and self.esito is Esito.IN_CORSO
                and (not self.timer_avviato or now < self.lampeggio_fino))

    def sposta_tempo(self, delta: int) -> None:
        self.tempo_inizio += delta
        self.tempo_fine_boost += delta
        self.vento.ultimo_cambio += delta
        self.barca.ultimo_danno += delta
        self.lampeggio_fino += delta
        if self.prossimo_fulmine > 0:
            self.prossimo_fulmine += delta

    def boost_attivo(self, now: int) -> bool:
        return now < self.tempo_fine_boost

    def _avvia_timer(self, now: int) -> None:
        self.timer_avviato = True
        self.tempo_inizio = now

    def attiva_boost(self, now: int) -> None:
        if self.esito is not Esito.IN_CORSO:
            return
        if self.pip_boost > 0 and now > self.tempo_fine_boost:
            if not self.timer_avviato:
                self._avvia_timer(now)
            self.pip_boost -= 1
            self.tempo_fine_boost = now + DURATA_BOOST
            self.audio.play("boost")
            self.fx.getto_boost(self.barca.x, self.barca.y)

    def _concludi(self, esito: Esito, motivo: str = "") -> None:
        if self.esito is not Esito.IN_CORSO:
            return
        self.esito = esito
        self.motivo = motivo
        self.audio.ferma_ost_livello()
        self.audio.play("gameover" if esito is Esito.DISTRUTTA else "vittoria")
        b = self.barca
        if esito is Esito.DISTRUTTA:
            self.fx.esplosione(b.x, b.y, grande=True)
        else:
            self.fx.scintille(b.x, b.y)

    def _danno(self, now: int, gioco_ref=None) -> None:
        b = self.barca
        if not b.puo_subire_danno(now):
            return
        b.vite -= 1
        b.ultimo_danno = now
        self.danni_subiti += 1

        if gioco_ref:
            gioco_ref.attiva_screen_shake(12, 10)
            gioco_ref.attiva_hit_stop(3)

        if self.punti_monete > 0:
            self._aggiungi_testo_fluttuante(b.x, b.y, f"-{self.punti_monete}", (255, 50, 50))
        self.punti -= self.punti_monete
        self.monete_raccolte_livello = 0
        self.punti_monete = 0

        self.audio.play("danno")
        self.fx.schizzo(b.x, b.y, 10, 2.5)
        self.fx.detriti(b.x, b.y, 6)
        if b.vite <= 0:
            self._concludi(Esito.DISTRUTTA, "avaria")

    def _esplosione_barile_rosso(self, barile, now, gioco_ref=None) -> None:
        self._danno(now, gioco_ref)
        self.audio.play("esplosione")
        self.fx.esplosione(barile.x, barile.y)
        if barile in self.barili:
            self.barili.remove(barile)
        if self.esito is not Esito.IN_CORSO:
            return
        self.barca.x = float(self.porto_a[0])
        self.barca.y = float(self.porto_a[1])
        self.barca.velocita = 0.0

    def aggiorna(self, dt: float, now: int, tasti, gioco_ref=None) -> None:
        f = dt * FPS if USA_DELTA_TIME else 1.0
        b = self.barca
        b.vela_verso(self.vento.angolo, f)
        self.fx.aggiorna(f)

        testi_attivi = []
        for tf in self.testi_fluttuanti:
            tf["y"] -= 1.0
            tf["vita"] -= f
            if tf["vita"] > 0:
                testi_attivi.append(tf)
        self.testi_fluttuanti = testi_attivi

        if self.atmosfera.nuvole:
            rad_v = math.radians(self.vento.angolo)
            vx_n = math.sin(rad_v) * (0.2 + 0.1 * self.vento.forza)
            vy_n = -math.cos(rad_v) * (0.2 + 0.1 * self.vento.forza)
            for n in self.nuvole:
                n["x"] += vx_n * f
                n["y"] += vy_n * f
                if n["x"] < -n["rx"] * 2:
                    n["x"] = LARGHEZZA + n["rx"]
                elif n["x"] > LARGHEZZA + n["rx"] * 2:
                    n["x"] = -n["rx"]
                if n["y"] < HUD_ALTO:
                    n["y"] = HUD_BASSO_Y - 10
                elif n["y"] > HUD_BASSO_Y:
                    n["y"] = HUD_ALTO + 10

        if self.atmosfera.pioggia:
            for g in self.gocce_pioggia:
                g["x"] += 2 * f
                g["y"] += g["vel"] * f
                if g["y"] > HUD_BASSO_Y or g["x"] > LARGHEZZA:
                    g["x"] = random.randint(0, LARGHEZZA)
                    g["y"] = HUD_ALTO

        if self.flash_fulmine_timer > 0:
            self.flash_fulmine_timer -= 1
        elif self.atmosfera.fulmini and EFFETTI_ATTIVI and now >= self.prossimo_fulmine:
            self.flash_fulmine_timer = random.randint(3, 6)
            
            # Frequenza dei fulmini velocizzata se siamo nei livelli 28, 29 o 30
            next_min = 2000 if self.numero >= 28 else FULMINE_NEXT_MIN_MS
            next_max = 4500 if self.numero >= 28 else FULMINE_NEXT_MAX_MS
            self.prossimo_fulmine = now + random.randint(next_min, next_max)
            
            self.audio.play("tuono")
            if gioco_ref:
                gioco_ref.attiva_screen_shake(8, 6)

        if self.esito is not Esito.IN_CORSO:
            return

        if not self.timer_avviato and (
            tasti[pygame.K_LEFT] or tasti[pygame.K_RIGHT] or tasti[pygame.K_UP]
        ):
            self._avvia_timer(now)

        if self.timer_avviato:
            trascorso = now - self.tempo_inizio
            limite = self.cfg.secondi * 1000
            sec_prec = self.secondi_rimanenti
            self.secondi_rimanenti = max(0, int((limite - trascorso) / 1000))
            if self.secondi_rimanenti < sec_prec and self.secondi_rimanenti <= 5:
                self.audio.play("tic")
            if trascorso > limite:
                self._concludi(Esito.DISTRUTTA, "tempo_scaduto")
                return

        if self.vento.scaduto(now):
            self.vento.cambia(self.cfg.forza_max, now)

        boost = self.boost_attivo(now)
        self._muovi_barca(f, boost)
        self._muovi_barili(f)
        self._scie_barili(f)
        self._spruzzi_ostacoli(f)
        self._collisioni(now, boost, gioco_ref)
        b.limita_allo_schermo()

    def _velocita_massima(self, diff: float, boost: bool) -> tuple[float, str]:
        forza = self.vento.forza
        if boost:
            return 4.5, "BOOST ATTIVO!"
        if diff < 45:
            return 4.0 + forza * 0.3, "Vento in Poppa!"
        if diff > 135:
            if forza == 5:
                return 0.05, "TEMPESTA LVL 5: Accelerazione bloccata!"
            if forza == 6:
                return 0.8, "TEMPESTA LVL 6: Deriva forzata!"
            return max(0.2, 1.5 - forza * 0.25), "Controvento!"
        return 2.5, "Vento di Traverso"

    def _muovi_barca(self, f: float, boost: bool) -> None:
        b, vento = self.barca, self.vento
        tasti = pygame.key.get_pressed()
        x0, y0 = b.x, b.y

        if tasti[pygame.K_LEFT]:
            b.angolo -= VELOCITA_ANGOLARE * f
        if tasti[pygame.K_RIGHT]:
            b.angolo += VELOCITA_ANGOLARE * f
        b.angolo %= 360

        diff = abs((b.angolo - vento.angolo + 180) % 360 - 180)
        v_max, self.stato_vela = self._velocita_massima(diff, boost)
        tempesta_f5 = (not boost) and vento.forza == 5 and diff > 135

        if tasti[pygame.K_UP]:
            if tempesta_f5:
                b.velocita *= ATTRITO ** f
            elif b.velocita < v_max:
                b.velocita += ACCELERAZIONE * f
        else:
            b.velocita *= ATTRITO ** f
            if b.velocita < 0.05:
                b.velocita = 0.0

        if b.velocita > 0:
            b.avanza(b.angolo, b.velocita * f)

        if self.timer_avviato and not boost and not tempesta_f5:
            spinta = 0.35 if vento.forza == 6 else 0.2 * vento.forza
            b.avanza(vento.angolo, spinta * f)

        self._emetti_scia(math.hypot(b.x - x0, b.y - y0) / max(f, 1e-6), boost, f)

    def _muovi_barili(self, f: float) -> None:
        vento = self.vento
        rad = math.radians(vento.angolo)
        perp = rad + math.pi / 2
        ostacoli = self.isole + self.scogli
        attrito = IMPULSO_ATTRITO ** f

        for barile in self.barili:
            barile.fase += 0.05 * f
            spinta = (0.3 + vento.forza * 0.15) * barile.velocita_extra
            zigzag = math.sin(barile.fase) * 0.8
            deriva_x = spinta * math.sin(rad) + zigzag * math.cos(perp)
            deriva_y = -(spinta * math.cos(rad) - zigzag * math.sin(perp))
            barile.vx = deriva_x + barile.ix
            barile.vy = deriva_y + barile.iy
            barile.x += barile.vx * f
            barile.y += barile.vy * f
            barile.ix *= attrito
            barile.iy *= attrito
            barile.pausa_fx = max(0.0, barile.pausa_fx - f)

            for o in ostacoli:
                minimo = o.raggio + barile.raggio
                if math.hypot(barile.x - o.x, barile.y - o.y) >= minimo:
                    continue
                ang = math.atan2(barile.y - o.y, barile.x - o.x)
                nx, ny = math.cos(ang), math.sin(ang)
                barile.x = o.x + nx * (minimo + 2)
                barile.y = o.y + ny * (minimo + 2)
                urto = -(barile.vx * nx + barile.vy * ny)
                if urto > 0:
                    barile.ix += nx * urto * RIMBALZO_OSTACOLI
                    barile.iy += ny * urto * RIMBALZO_OSTACOLI
                    if urto > 0.35 and barile.pausa_fx <= 0:
                        self.fx.schizzo(o.x + nx * o.raggio, o.y + ny * o.raggio,
                                        5 + int(urto * 4), 1.5 + urto)
                        barile.pausa_fx = 25

        self._urti_barili()

        for barile in list(self.barili):
            bordo = self._bordo_uscita(barile)
            if bordo:
                self.barili.remove(barile)
                for _ in range(random.randint(0, 3)):
                    self.barili.append(
                        self._barile_rientrante(bordo, self.numero >= LIVELLO_BARILI_ROSSI))

    def _urti_barili(self) -> None:
        barili = self.barili
        for i in range(len(barili)):
            a = barili[i]
            for j in range(i + 1, len(barili)):
                c = barili[j]
                dx, dy = a.x - c.x, a.y - c.y
                dist = math.hypot(dx, dy)
                minimo = a.raggio + c.raggio
                if dist >= minimo:
                    continue
                if dist < 1e-6:
                    ang = random.uniform(0, 2 * math.pi)
                    nx, ny, dist = math.cos(ang), math.sin(ang), 0.0
                else:
                    nx, ny = dx / dist, dy / dist

                spostamento = (minimo - dist) * 0.6 / 2
                a.x += nx * spostamento
                a.y += ny * spostamento
                c.x -= nx * spostamento
                c.y -= ny * spostamento

                vrel = (a.vx - c.vx) * nx + (a.vy - c.vy) * ny
                if vrel < 0:
                    j_imp = -(1 + RESTITUZIONE_BARILI) * vrel / 2
                    a.ix += j_imp * nx
                    a.iy += j_imp * ny
                    c.ix -= j_imp * nx
                    c.iy -= j_imp * ny
                    if -vrel > 0.3 and a.pausa_fx <= 0 and c.pausa_fx <= 0:
                        self.fx.schizzo((a.x + c.x) / 2, (a.y + c.y) / 2,
                                        5 + int(-vrel * 3), 1.2 + -vrel)
                        a.pausa_fx = c.pausa_fx = 20

    def _emetti_scia(self, velocita: float, boost: bool, f: float) -> None:
        if velocita < 0.25:
            return
        self._acc_scia += velocita * (0.9 if boost else 0.5) * f
        b = self.barca
        rad = math.radians(b.angolo)
        hx, hy = math.sin(rad), -math.cos(rad)
        for _ in range(3):
            if self._acc_scia < 1:
                break
            self._acc_scia -= 1
            self.fx.schiuma_scia(b.x - hx * 22, b.y - hy * 22, -hy, hx, boost)

    def _scie_barili(self, f: float) -> None:
        for barile in self.barili:
            v = math.hypot(barile.vx, barile.vy)
            if v > 0.2 and random.random() < min(1.0, 0.2 * v * f):
                self.fx.scia_barile(barile.x - barile.vx / v * barile.raggio,
                                    barile.y - barile.vy / v * barile.raggio)

    def _spruzzi_ostacoli(self, f: float) -> None:
        if not EFFETTI_ATTIVI:
            return
        rad = math.radians(self.vento.angolo)
        vx, vy = math.sin(rad), -math.cos(rad)
        theta0 = math.atan2(-vy, -vx)
        forza = self.vento.forza
        for ostacoli, prob in ((self.isole, 0.025), (self.scogli, 0.018)):
            for o in ostacoli:
                if random.random() < prob * forza * f:
                    theta = theta0 + random.uniform(-0.9, 0.9)
                    self.fx.spruzzo(o.x + math.cos(theta) * o.raggio,
                                    o.y + math.sin(theta) * o.raggio,
                                    vx * 0.8 + random.uniform(-.2, .2),
                                    vy * 0.8 + random.uniform(-.2, .2))

    @staticmethod
    def _bordo_uscita(barile: Barile) -> str:
        if barile.x < -30:
            return "sinistra"
        if barile.x > LARGHEZZA + 30:
            return "destra"
        if barile.y < HUD_ALTO - barile.raggio:
            return "sopra"
        if barile.y > HUD_BASSO_Y + barile.raggio:
            return "sotto"
        return ""

    @staticmethod
    def _barile_rientrante(bordo_uscita: str, tutti_rossi: bool = False) -> Barile:
        y_min, y_max = HUD_ALTO + 10, HUD_BASSO_Y - 20
        if bordo_uscita == "sinistra":
            x, y = LARGHEZZA - 10, random.randint(y_min, y_max)
        elif bordo_uscita == "destra":
            x, y = 10, random.randint(y_min, y_max)
        elif bordo_uscita == "sopra":
            x, y = random.randint(50, 950), y_max
        else:
            x, y = random.randint(50, 950), y_min
        return Barile.casuale(x, y, 1.4, rosso=True if tutti_rossi else None)

    def _collisioni(self, now: int, boost: bool, gioco_ref=None) -> None:
        if self._collisione_porto():
            return
        self._collisione_monete()
        self._collisione_ostacoli(now, boost, gioco_ref)
        if self.esito is not Esito.IN_CORSO:
            return
        self._collisione_barili(now, boost, gioco_ref)

    def _collisione_porto(self) -> bool:
        b = self.barca
        px, py = self.porto_b
        dx = b.x - px
        dy = b.y - py
        if dx * dx + dy * dy < RAGGIO_PORTO_B * RAGGIO_PORTO_B:
            b.velocita = 0.0
            b.respingi_da(px, py, RAGGIO_PORTO_B)
            self._concludi(
                Esito.COMPLETATO if self.numero >= LIVELLO_FINALE else Esito.SUPERATO
            )
            return True
        return False

    def _collisione_monete(self) -> None:
        b = self.barca
        for m in self.monete[:]:
            if math.hypot(b.x - m["x"], b.y - m["y"]) < (m["raggio"] + RAGGIO_BARCA):
                self.monete_raccolte_livello += 1
                combo = self.monete_raccolte_livello
                moltiplicatore_combo = 1.25 ** (combo - 1)
                punti_moneta = int(50 * moltiplicatore_combo)

                self.punti_monete += punti_moneta
                self.punti += punti_moneta
                
                txt_popup = f"+{punti_moneta}"
                if combo > 1:
                    txt_popup += f" COMBO x{combo}!"
                self._aggiungi_testo_fluttuante(m["x"], m["y"], txt_popup, COLORE_ORO)

                self.audio.play("moneta")
                self.fx.scintille(m["x"], m["y"])
                self.monete.remove(m)

    def _collisione_ostacoli(self, now: int, boost: bool, gioco_ref=None) -> None:
        b = self.barca
        for o in self.isole + self.scogli:
            if math.hypot(b.x - o.x, b.y - o.y) < o.raggio:
                if boost:
                    b.velocita = 0.0
                    b.respingi_da(o.x, o.y, o.raggio)
                else:
                    self._danno(now, gioco_ref)
                    b.velocita = 0.0
                    b.respingi_da(o.x, o.y, o.raggio)

    def _collisione_barili(self, now: int, boost: bool, gioco_ref=None) -> None:
        b = self.barca
        for barile in list(self.barili):
            somma_raggi = barile.raggio + RAGGIO_BARCA
            if math.hypot(b.x - barile.x, b.y - barile.y) >= somma_raggi:
                continue

            if barile.rosso:
                if b.puo_subire_danno(now):
                    if gioco_ref:
                        gioco_ref.attiva_screen_shake(18, 14)
                        gioco_ref.attiva_hit_stop(4)
                    self._esplosione_barile_rosso(barile, now, gioco_ref)
                    if b.vite <= 0:
                        self._concludi(Esito.DISTRUTTA, "esplosione")
                        return
            else:
                if boost:
                    ang = math.atan2(b.y - barile.y, b.x - barile.x)
                    nx, ny = -math.cos(ang), -math.sin(ang)
                    b.velocita *= 0.5
                    b.respingi_da(barile.x, barile.y, somma_raggi)
                    barile.x += nx * 6
                    barile.y += ny * 6
                else:
                    self._danno(now, gioco_ref)
                    ang = math.atan2(b.y - barile.y, b.x - barile.x)
                    nx, ny = -math.cos(ang), -math.sin(ang)
                    v_urto = b.velocita
                    b.velocita *= 0.2
                    b.respingi_da(barile.x, barile.y, somma_raggi)
                    barile.x += nx * 8
                    barile.y += ny * 8
                    barile.ix += nx * 0.35 * v_urto
                    barile.iy += ny * 0.35 * v_urto
                    if barile.pausa_fx <= 0:
                        self.fx.schizzo(barile.x - nx * barile.raggio,
                                        barile.y - ny * barile.raggio,
                                        8, 2.0 + 0.3 * v_urto)
                        barile.pausa_fx = 20
                if self.esito is not Esito.IN_CORSO:
                    return


# ---------------------------------------------------------------------------
# CLASSIFICA
# ---------------------------------------------------------------------------
class Classifica:
    def __init__(self, percorso: str = FILE_CLASSIFICA) -> None:
        self.percorso = percorso
        self.voci: list[dict] = []
        self._carica()

    def _carica(self) -> None:
        try:
            with open(self.percorso, encoding="utf-8") as f:
                dati = json.load(f)
            voci = [
                {"nick": str(v["nick"])[:LUNGHEZZA_NICK].upper(), "punti": int(v["punti"])}
                for v in dati
            ]
            voci.sort(key=lambda v: v["punti"], reverse=True)
            self.voci = voci[:POSTI_CLASSIFICA]
        except (OSError, ValueError, KeyError, TypeError):
            self.voci = []

    def _salva(self) -> None:
        try:
            with open(self.percorso, "w", encoding="utf-8") as f:
                json.dump(self.voci, f, indent=2)
        except OSError:
            pass

    def qualifica(self, punti: int) -> bool:
        if punti <= 0:
            return False
        if len(self.voci) < POSTI_CLASSIFICA:
            return True
        return punti > self.voci[-1]["punti"]

    def posto_per(self, punti: int) -> int:
        return sum(1 for v in self.voci if v["punti"] >= punti)

    def inserisci(self, nick: str, punti: int) -> int:
        posto = sum(1 for v in self.voci if v["punti"] >= punti)
        self.voci.insert(posto, {"nick": nick.upper()[:LUNGHEZZA_NICK], "punti": punti})
        del self.voci[POSTI_CLASSIFICA:]
        self._salva()
        return posto

    @property
    def high_score(self) -> int:
        return self.voci[0]["punti"] if self.voci else 1000


# ---------------------------------------------------------------------------
# GRAFICA DECORATIVA
# ---------------------------------------------------------------------------
def _crea_cappello() -> pygame.Surface:
    s = pygame.Surface((160, 100), pygame.SRCALPHA)
    nero, nero_chiaro, osso = (22, 22, 30), (45, 45, 58), (240, 240, 240)

    tesa = [(4, 56), (30, 42), (46, 62), (80, 70), (114, 62), (130, 42), (156, 56),
            (146, 80), (112, 92), (80, 94), (48, 92), (14, 80)]
    pygame.draw.polygon(s, nero_chiaro, tesa)
    pygame.draw.polygon(s, (0, 0, 0), tesa, 2)
    pygame.draw.lines(s, COLORE_ORO, False,
                      [(16, 76), (48, 88), (80, 90), (112, 88), (144, 76)], 3)

    calotta = [(36, 64), (44, 30), (60, 12), (80, 8), (100, 12), (116, 30), (124, 64), (80, 72)]
    pygame.draw.polygon(s, nero, calotta)
    pygame.draw.polygon(s, (0, 0, 0), calotta, 2)

    pygame.draw.circle(s, osso, (80, 36), 12)
    pygame.draw.rect(s, osso, (72, 44, 16, 10), border_radius=3)
    pygame.draw.circle(s, (0, 0, 0), (75, 36), 3)
    pygame.draw.circle(s, (0, 0, 0), (85, 36), 3)
    pygame.draw.polygon(s, (0, 0, 0), [(80, 40), (78, 45), (82, 45)])
    for x in (76, 80, 84):
        pygame.draw.line(s, (120, 120, 120), (x, 48), (x, 53), 1)

    for a, b in (((60, 76), (100, 90)), ((100, 76), (60, 90))):
        pygame.draw.line(s, osso, a, b, 4)
        pygame.draw.circle(s, osso, a, 3)
        pygame.draw.circle(s, osso, b, 3)
    return s


def disegna_teschio_arcade(surface: pygame.Surface, x: int, y: int, attivo: bool = True):
    colore_testa = (230, 230, 230) if attivo else COLORE_SPENTO
    colore_occhi = (0, 0, 0) if attivo else (40, 40, 40)
    pygame.draw.circle(surface, colore_testa, (x, y), 8)
    pygame.draw.rect(surface, colore_testa, (x - 4, y + 3, 8, 7), border_radius=1)
    pygame.draw.circle(surface, colore_occhi, (x - 3, y - 1), 2)
    pygame.draw.circle(surface, colore_occhi, (x + 3, y - 1), 2)
    pygame.draw.polygon(surface, colore_occhi, [(x, y + 2), (x - 1, y + 4), (x + 1, y + 4)])


# ---------------------------------------------------------------------------
# GIOCO
# ---------------------------------------------------------------------------
COMANDI = [
    ("FRECCIA SINISTRA / DESTRA", "Ruota il timone della barca"),
    ("FRECCIA SU", "Accelera!"),
    ("BARRA SPAZIATRICE", "Boost: scudo da vento e danni, ma ATTENZIONE AI BARILI ROSSI!"),
    ("TASTO [C]", "Attiva / disattiva il filtro retro CRT 4:3 con schermo curvo"),
    ("TASTO [ENTER]", "Avvia la partita / Passa al livello successivo"),
    ("TASTO [L]", "Mostra la classifica (Title Screen, Game Over e fine gioco)"),
    ("OBIETTIVO GIOCO", "Raggiungi il Porto B raccogliendo monete ed evitando i pericoli!"),
]


OPZIONI_PAUSA = [
    "Riprendi gioco",
    "Filtro CRT: ",  # Dinamico
    "Riparti dal livello 1",
    "Ritorna alla schermata principale",
    "Esci a Desktop",
]


class Gioco:
    def __init__(self) -> None:
        pygame.init()
        self.audio = Audio()
        self.schermo = pygame.display.set_mode((LARGHEZZA, ALTEZZA))
        pygame.display.set_caption("THE PIRATINZ Arcade Edition")
        self.orologio = pygame.time.Clock()

        self.surface_virtuale = pygame.Surface((LARGHEZZA, ALTEZZA))

        self.font = pygame.font.SysFont(None, 22)
        self.font_comando = pygame.font.SysFont(None, 20, bold=True)
        self.font_sottotitolo = pygame.font.SysFont(None, 28)
        self.font_grande = pygame.font.SysFont(None, 30, bold=True)
        self.font_timer = pygame.font.SysFont(None, 52, bold=True)
        self.font_titolo = pygame.font.SysFont(None, 48, bold=True)
        self.font_classifica = pygame.font.SysFont(None, 38, bold=True)
        self.font_nick = pygame.font.SysFont(None, 90, bold=True)
        self.font_record = pygame.font.SysFont(None, 92, bold=True)
        self.font_arcade = pygame.font.SysFont("Courier New", 20, bold=True)
        self.font_banner = pygame.font.SysFont(None, 64, bold=True)

        self._prepara_superfici()

        self.schermata = Schermata.TITLE
        self.in_esecuzione = True
        self.numero_livello = 1
        self.punteggio = 0
        self.livello = Livello(1, pygame.time.get_ticks(), self.audio)
        self.audio.avvia_title()

        self.classifica = Classifica()
        self.ultimo_input = pygame.time.get_ticks()
        self.classifica_ritorno = Schermata.TITLE
        self.classifica_inizio = 0
        self.classifica_auto = False
        self.nick_attivo = False
        self.nick = ["A"] * LUNGHEZZA_NICK
        self.nick_cursore = 0
        self.posto_evidenziato = None

        self.shake_intensita = 0
        self.shake_frame = 0
        self.hit_stop_frame = 0
        self.filtro_crt_attivo = True
        self.banner_frame = 0

        self.conteggio_bonus_attivo = False
        self.bonus_tempo_calc = 0
        self.bonus_perfetto_calc = 0
        self.timer_conteggio = 0

        self.in_pausa = False
        self.pausa_voce = 0
        self.pausa_inizio = 0
        self.transizione_inizio: int | None = None
        self.snap: pygame.Surface | None = None
        self.record_attivo = False
        self.record_t0 = 0
        self.record_fanfara_suonata = False
        self.record_posto = 0

    def _prepara_superfici(self) -> None:
        self.barra_alto = pygame.Surface((LARGHEZZA, HUD_ALTO), pygame.SRCALPHA)
        self.barra_alto.fill((0, 0, 0, 180))
        self.barra_basso = pygame.Surface((LARGHEZZA, ALTEZZA - HUD_BASSO_Y), pygame.SRCALPHA)
        self.barra_basso.fill((0, 0, 0, 190))

        self.strato_basso = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
        self.strato_alto = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)

        self.surf_scafo = pygame.Surface((60, 60), pygame.SRCALPHA)
        scafo = [(30, 5), (39, 18), (37, 52), (23, 52), (21, 18)]
        pygame.draw.polygon(self.surf_scafo, COLORE_SCAFO, scafo)
        pygame.draw.polygon(self.surf_scafo, COLORE_BORDO_SCAFO, scafo, 2)
        
        ponte = [(30, 10), (34, 18), (33, 48), (27, 48), (26, 18)]
        pygame.draw.polygon(self.surf_scafo, (160, 90, 40), ponte)

        cabina = pygame.Rect(21, 38, 20, 18)
        pygame.draw.rect(self.surf_scafo, (110, 55, 20), cabina)
        pygame.draw.rect(self.surf_scafo, (50, 25, 10), cabina, 2)
        pygame.draw.line(self.surf_scafo, (70, 35, 15), (23, 44), (37, 44), 1)

        pygame.draw.circle(self.surf_scafo, (40, 20, 5), (30, 16), 2)
        pygame.draw.circle(self.surf_scafo, (40, 20, 5), (30, 30), 3)
        pygame.draw.circle(self.surf_scafo, (40, 20, 5), (30, 44), 2)

        fiocco = [(30, 10), (25, 20), (35, 20)]
        pygame.draw.polygon(self.surf_scafo, COLORE_VELA, fiocco)
        pygame.draw.polygon(self.surf_scafo, COLORE_BORDO_VELA, fiocco, 1)

        poppa = [(30, 42), (26, 50), (34, 50)]
        pygame.draw.polygon(self.surf_scafo, COLORE_VELA, poppa)
        pygame.draw.polygon(self.surf_scafo, COLORE_BORDO_VELA, poppa, 1)

        self.surf_vela = pygame.Surface((60, 60), pygame.SRCALPHA)
        vela_centrale = [(30, 10), (60, 28), (39, 25), (21, 25), (0, 28)]
        vela_scalata = [(30 + (x - 30) * SCALA_VELA, 30 + (y - 30) * SCALA_VELA) for x, y in vela_centrale]
        
        pygame.draw.polygon(self.surf_vela, COLORE_VELA, vela_scalata)
        pygame.draw.polygon(self.surf_vela, COLORE_BORDO_VELA, vela_scalata, 2)
        
        punto_sinistro_scalato = (30 + (0 - 30) * SCALA_VELA, 30 + (28 - 30) * SCALA_VELA)
        punto_destro_scalato = (30 + (60 - 30) * SCALA_VELA, 30 + (28 - 30) * SCALA_VELA)
        pygame.draw.line(self.surf_vela, (139, 69, 19), punto_sinistro_scalato, punto_destro_scalato, 2)

        self.cappello = _crea_cappello()
        self.cappello_hud = pygame.transform.smoothscale(self.cappello, (44, 28))
        self.strato_mare_pixel = pygame.Surface((LARGHEZZA, ALTEZZA_MARE_PIXEL), pygame.SRCALPHA)
        self.velo = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)

        self.flash_fulmine = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
        self.flash_fulmine.fill((255, 255, 255, 140))

        self.surf_crt = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
        for y in range(0, ALTEZZA, 3):
            pygame.draw.line(self.surf_crt, (0, 0, 0, 50), (0, y), (LARGHEZZA, y))

        maschera = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
        maschera.fill((0, 0, 0, 255))
        rect_crt = pygame.Rect(70, 45, LARGHEZZA - 140, ALTEZZA - 90)
        pygame.draw.rect(maschera, (0, 0, 0, 0), rect_crt, border_radius=45)
        
        for i in range(15):
            r = rect_crt.inflate(-i * 2, -i * 2)
            pygame.draw.rect(maschera, (0, 0, 0, 14), r, border_radius=40)

        self.surf_crt.blit(maschera, (0, 0))

    def attiva_screen_shake(self, intensita: int = 10, frame: int = 8) -> None:
        self.shake_intensita = intensita
        self.shake_frame = frame

    def attiva_hit_stop(self, frame: int = 3) -> None:
        self.hit_stop_frame = frame

    def esegui(self) -> None:
        while self.in_esecuzione:
            dt = min(self.orologio.tick(FPS) / 1000, 0.05)
            now = pygame.time.get_ticks()

            self._gestisci_eventi(now)

            if self.hit_stop_frame > 0:
                self.hit_stop_frame -= 1
            elif (self.schermata is Schermata.GIOCO and not self.in_pausa
                  and self.transizione_inizio is None):
                self._aggiorna(dt, now)

            self._controlla_inattivita(now)

            offset_x, offset_y = 0, 0
            if self.shake_frame > 0:
                self.shake_frame -= 1
                offset_x = random.randint(-self.shake_intensita, self.shake_intensita)
                offset_y = random.randint(-self.shake_intensita, self.shake_intensita)

            if self.schermata is Schermata.TITLE:
                self._disegna_title(now)
            elif self.schermata is Schermata.ISTRUZIONI:
                self._disegna_istruzioni(now)
            elif self.schermata is Schermata.CLASSIFICA:
                self._disegna_classifica(now)
            elif self.in_pausa:
                self._disegna_gioco(self.pausa_inizio)
                self._disegna_pausa()
            else:
                self._disegna_gioco(now)
                if self.transizione_inizio is not None:
                    self._disegna_transizione(now)

            self.schermo.fill((0, 0, 0))

            if self.filtro_crt_attivo:
                gioco_scalato = pygame.transform.smoothscale(
                    self.surface_virtuale, (LARGHEZZA - 140, ALTEZZA - 90)
                )
                self.schermo.blit(gioco_scalato, (70 + offset_x, 45 + offset_y))
                self.schermo.blit(self.surf_crt, (0, 0))
            else:
                self.schermo.blit(self.surface_virtuale, (offset_x, offset_y))

            pygame.display.flip()
        pygame.quit()

    def _carica_livello(self, numero: int, musica: bool = True) -> None:
        self.numero_livello = numero
        self.livello = Livello(numero, pygame.time.get_ticks(), self.audio)
        self.banner_frame = 90
        self.conteggio_bonus_attivo = False
        if musica:
            self.audio.avvia_ost_livello(numero, epica=numero >= LIVELLO_OST_EPICA)

    def _nuova_partita(self, musica: bool = True) -> None:
        self.punteggio = 0
        self._carica_livello(1, musica)

    def _apri_classifica(self, now: int, auto: bool = False, evidenzia=None) -> None:
        self.classifica_ritorno = self.schermata
        self.classifica_inizio = now
        self.classifica_auto = auto
        self.posto_evidenziato = evidenzia
        self.schermata = Schermata.CLASSIFICA

    def _chiudi_classifica(self, now: int) -> None:
        self.schermata = self.classifica_ritorno
        self.posto_evidenziato = None
        self.ultimo_input = now

    def _controlla_inattivita(self, now: int) -> None:
        if self.schermata is Schermata.TITLE:
            if now - self.ultimo_input >= ATTESA_CLASSIFICA_MS:
                self._apri_classifica(now, auto=True)
        elif self.schermata is Schermata.CLASSIFICA and self.classifica_auto:
            if now - self.classifica_inizio >= DURATA_CLASSIFICA_AUTO_MS:
                self._chiudi_classifica(now)

    def _apri_pausa(self, now: int) -> None:
        self.in_pausa = True
        self.pausa_voce = 0
        self.pausa_inizio = now
        self.audio.pausa()

    def _chiudi_pausa(self, now: int) -> None:
        self.livello.sposta_tempo(now - self.pausa_inizio)
        self.in_pausa = False
        self.audio.riprendi()

    def _tasto_pausa(self, tasto: int, now: int) -> None:
        if tasto == pygame.K_ESCAPE:
            self._chiudi_pausa(now)
        elif tasto == pygame.K_UP:
            self.pausa_voce = (self.pausa_voce - 1) % len(OPZIONI_PAUSA)
        elif tasto == pygame.K_DOWN:
            self.pausa_voce = (self.pausa_voce + 1) % len(OPZIONI_PAUSA)
        elif tasto in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_LEFT, pygame.K_RIGHT):
            self._scegli_pausa(now, tasto)

    def _scegli_pausa(self, now: int, tasto: int = pygame.K_RETURN) -> None:
        voce = self.pausa_voce
        if voce == 0:
            self._chiudi_pausa(now)
        elif voce == 1:
            self.filtro_crt_attivo = not self.filtro_crt_attivo
        elif voce == 2:
            self.in_pausa = False
            self.audio.riprendi()
            self._nuova_partita()
        elif voce == 3:
            self.in_pausa = False
            self.audio.riprendi()
            self.audio.ferma_ost_livello()
            self._nuova_partita(musica=False)
            self.schermata = Schermata.TITLE
            self.audio.avvia_title()
            self.ultimo_input = now
        elif voce == 4:
            self.in_esecuzione = False

    def _inizia_record(self, now: int) -> None:
        self.record_attivo = True
        self.record_t0 = now + RITARDO_RECORD_MS
        self.record_fanfara_suonata = False
        self.record_posto = self.classifica.posto_per(self.punteggio)

    def _termina_record(self) -> None:
        self.record_attivo = False
        self._inizia_inserimento_nick()

    def _inizia_inserimento_nick(self) -> None:
        self.nick_attivo = True
        self.nick = ["A"] * LUNGHEZZA_NICK
        self.nick_cursore = 0

    def _tasto_nick(self, tasto: int, now: int) -> None:
        if tasto == pygame.K_BACKSPACE:
            if self.nick_cursore > 0:
                self.nick_cursore -= 1
        elif tasto == pygame.K_LEFT:
            self.nick_cursore = max(0, self.nick_cursore - 1)
        elif tasto == pygame.K_RIGHT:
            self.nick_cursore = min(LUNGHEZZA_NICK - 1, self.nick_cursore + 1)
        elif tasto in (pygame.K_UP, pygame.K_DOWN):
            passo = 1 if tasto == pygame.K_UP else -1
            c = ord(self.nick[self.nick_cursore]) - ord("A")
            self.nick[self.nick_cursore] = chr(ord("A") + (c + passo) % 26)
        elif pygame.K_a <= tasto <= pygame.K_z:
            self.nick[self.nick_cursore] = chr(ord("A") + tasto - pygame.K_a)
            self.nick_cursore = min(LUNGHEZZA_NICK - 1, self.nick_cursore + 1)
        elif tasto in (pygame.K_RETURN, pygame.K_KP_ENTER):
            posto = self.classifica.inserisci("".join(self.nick), self.punteggio)
            self.nick_attivo = False
            self._apri_classifica(now, evidenzia=posto)

    def _gestisci_eventi(self, now: int) -> None:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.in_esecuzione = False
            elif evento.type == pygame.KEYDOWN:
                self.ultimo_input = now
                if evento.key == pygame.K_c:
                    self.filtro_crt_attivo = not self.filtro_crt_attivo
                self._tasto_premuto(evento.key, now)

    def _tasto_premuto(self, tasto: int, now: int) -> None:
        if self.schermata is Schermata.CLASSIFICA:
            if tasto == pygame.K_RETURN and self.classifica_ritorno is Schermata.TITLE:
                self.audio.play("aaargh")
                self.schermata = Schermata.ISTRUZIONI
                self.posto_evidenziato = None
            else:
                self._chiudi_classifica(now)

        elif self.schermata is Schermata.TITLE:
            if tasto == pygame.K_RETURN:
                self.audio.play("aaargh")
                self.schermata = Schermata.ISTRUZIONI
            elif tasto == pygame.K_l:
                self._apri_classifica(now)
            elif tasto == pygame.K_ESCAPE:
                self.in_esecuzione = False

        elif self.schermata is Schermata.ISTRUZIONI:
            if tasto == pygame.K_ESCAPE:
                self.schermata = Schermata.TITLE
            elif tasto == pygame.K_RETURN:
                self.snap = self.surface_virtuale.copy()
                self.audio.ferma_title()
                self.schermata = Schermata.GIOCO
                self._nuova_partita()
                self.transizione_inizio = now
                self.livello.lampeggio_fino += DURATA_TRANSIZIONE_MS

        elif self.schermata is Schermata.GIOCO:
            if self.transizione_inizio is not None:
                return
            if self.in_pausa:
                self._tasto_pausa(tasto, now)
                return
            esito = self.livello.esito
            if self.record_attivo:
                if now - self.record_t0 >= SKIP_RECORD_DOPO_MS and tasto != pygame.K_ESCAPE:
                    self._termina_record()
                return
            if self.nick_attivo:
                self._tasto_nick(tasto, now)
                return
            if tasto == pygame.K_ESCAPE:
                self._apri_pausa(now)
                return
            if tasto == pygame.K_l and esito in (Esito.DISTRUTTA, Esito.COMPLETATO):
                self._apri_classifica(now)
            elif tasto == pygame.K_RETURN:
                if esito is Esito.COMPLETATO:
                    self.schermata = Schermata.TITLE
                    self._nuova_partita(musica=False)
                    self.audio.avvia_title()
                elif esito is Esito.SUPERATO:
                    self._carica_livello(self.numero_livello + 1)
                elif esito is Esito.DISTRUTTA:
                    self._nuova_partita()
            elif tasto == pygame.K_SPACE:
                self.livello.attiva_boost(now)

    def _aggiorna(self, dt: float, now: int) -> None:
        lv = self.livello
        era_in_corso = lv.esito is Esito.IN_CORSO
        lv.aggiorna(dt, now, pygame.key.get_pressed(), gioco_ref=self)

        if self.banner_frame > 0:
            self.banner_frame -= 1

        if era_in_corso and lv.esito in (Esito.SUPERATO, Esito.COMPLETATO):
            self.conteggio_bonus_attivo = True
            self.bonus_tempo_calc = int(lv.secondi_rimanenti * 10 * lv.cfg.moltiplicatore)
            
            self.bonus_perfetto_calc = 0
            if lv.danni_subiti == 0:
                self.bonus_perfetto_calc += 200
            if lv.monete_raccolte_livello == lv.monete_totali_livello and lv.monete_totali_livello > 0:
                self.bonus_perfetto_calc += 300

            self.timer_conteggio = 0

        if self.conteggio_bonus_attivo:
            self.timer_conteggio += 1
            if self.timer_conteggio % 2 == 0:
                stacco = 10
                if self.bonus_tempo_calc > 0:
                    prog = min(stacco, self.bonus_tempo_calc)
                    self.bonus_tempo_calc -= prog
                    self.punteggio += prog
                    self.audio.play("tic")
                elif self.bonus_perfetto_calc > 0:
                    prog = min(stacco, self.bonus_perfetto_calc)
                    self.bonus_perfetto_calc -= prog
                    self.punteggio += prog
                    self.audio.play("tic")
                else:
                    self.conteggio_bonus_attivo = False

        if era_in_corso and lv.esito in (Esito.DISTRUTTA, Esito.COMPLETATO):
            if self.classifica.qualifica(self.punteggio):
                self._inizia_record(now)

        if self.record_attivo:
            if now >= self.record_t0 and not self.record_fanfara_suonata:
                self.record_fanfara_suonata = True
                self.audio.play("fanfara")
            if now - self.record_t0 >= DURATA_RECORD_MS:
                self._termina_record()

    def _testo(self, font, testo, colore, centro=None, topleft=None) -> None:
        s = font.render(testo, True, colore)
        rect = s.get_rect(center=centro) if centro else s.get_rect(topleft=topleft)
        self.surface_virtuale.blit(s, rect)

    def _pannello(self, larghezza: int, altezza: int, alpha: int) -> None:
        s = pygame.Surface((larghezza, altezza), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        self.surface_virtuale.blit(s, s.get_rect(center=(500, 320)))

    def _disegna_mare_pixel(self, now: int) -> None:
        t = now / 1000
        p, b = self.strato_mare_pixel, PIXEL_MARE
        h = ALTEZZA_MARE_PIXEL
        p.fill((0, 0, 0, 0))
        for c in range(LARGHEZZA // b):
            onda = math.sin(c * 0.45 + t * 1.6) * 1.2 + math.sin(c * 0.17 - t * 0.9) * 0.9
            y0 = (2 + int(round(onda))) * b
            x = c * b
            pygame.draw.rect(p, (215, 238, 255, 95), (x, y0, b, b))
            pygame.draw.rect(p, (90, 170, 240, 80), (x, y0 + b, b, b))
            if y0 + 2 * b < h:
                pygame.draw.rect(p, (45, 120, 215, 75), (x, y0 + 2 * b, b, min(2 * b, h - y0 - 2 * b)))
            if y0 + 4 * b < h:
                pygame.draw.rect(p, (25, 85, 175, 75), (x, y0 + 4 * b, b, h - y0 - 4 * b))
            if (c + int(t * 3)) % 6 < 2:
                pygame.draw.rect(p, (130, 200, 255, 70), (x, y0 + 2 * b, b, b // 2))
        self.surface_virtuale.blit(p, (0, ALTEZZA - h))

    def _disegna_title(self, now: int) -> None:
        self.surface_virtuale.fill((10, 25, 45))
        self._disegna_mare_pixel(now)
        self.surface_virtuale.blit(self.cappello, self.cappello.get_rect(
            center=(500, 170 + int(math.sin(now / 600) * 4))))
        self._testo(self.font_titolo, "THE PIRATINZ!", COLORE_ORO, centro=(500, 260))
        self._testo(self.font_sottotitolo, "Le avventure di Captain CIR'Z ed il suo fedele TONIPu'zz!",
                    (200, 220, 240), centro=(500, 330))
        if (now // 400) % 2 == 0:
            self._testo(self.font_grande, "PRESS START [ENTER]", COLORE_TESTO,
                        centro=(500, 430))
        self._testo(self.font, "[L] CLASSIFICA   -   [C] FILTRO CRT", (150, 180, 210), centro=(500, 480))

    def _disegna_classifica(self, now: int) -> None:
        self.surface_virtuale.fill((10, 25, 45))
        t = (now - self.classifica_inizio) / 1000
        voci = self.classifica.voci

        for k in range(3):
            y0 = 560 + k * 40
            punti = [(x, y0 + math.sin(x / 70 + t * (1.5 + k * 0.4) + k) * 10)
                     for x in range(0, LARGHEZZA + 20, 20)]
            punti += [(LARGHEZZA, ALTEZZA), (0, ALTEZZA)]
            pygame.draw.polygon(self.surface_virtuale, (15 + k * 8, 50 + k * 14, 100 + k * 18), punti)

        self._testo(self.font_titolo, "CLASSIFICA - TOP 10", COLORE_ORO,
                    centro=(500, int(65 + math.sin(t * 2.5) * 6)))

        colori_podio = [COLORE_ORO, (210, 210, 220), (205, 127, 50)]
        for i in range(POSTI_CLASSIFICA):
            ritardo = i * 0.12
            avanzamento = max(0.0, min(1.0, (t - ritardo) / 0.9))
            entrata = (1 - avanzamento) ** 3 * 1100
            onda = math.sin(t * 3 + i * 0.7) * 14 * (0.35 + 0.65 * avanzamento)
            x_off = entrata + onda
            y = 130 + i * 46 + math.sin(t * 2.2 + i * 0.7) * 4

            if i < len(voci):
                nick, punti = voci[i]["nick"], voci[i]["punti"]
            else:
                nick, punti = "---", 0
            if i < len(voci):
                colore = colori_podio[i] if i < 3 else COLORE_TESTO
            else:
                colore = (90, 105, 125)
            if self.posto_evidenziato == i and (now // 250) % 2 == 0:
                colore = (0, 255, 255)

            self._testo(self.font_classifica, f"{i + 1:>2}.", colore, centro=(int(290 + x_off), int(y)))
            self._testo(self.font_classifica, nick, colore, centro=(int(430 + x_off), int(y)))
            self._testo(self.font_classifica, f"{punti:>7}" if i < len(voci) else "-------",
                        colore, centro=(int(640 + x_off), int(y)))

        if self.classifica_auto:
            msg = "Premi un tasto per tornare  -  [ENTER] per giocare"
        else:
            msg = "Premi un tasto per tornare indietro"
        if (now // 500) % 2 == 0:
            self._testo(self.font, msg, COLORE_TESTO, centro=(500, 660))

    def _disegna_inserimento_nick(self, now: int) -> None:
        self._pannello(640, 300, 230)
        esito_vittoria = self.livello.esito is Esito.COMPLETATO
        titolo = "HAI COMPLETATO IL GIOCO!" if esito_vittoria else "NUOVO RECORD!"
        self._testo(self.font_grande, titolo, COLORE_ORO, centro=(500, 205))
        self._testo(self.font, f"Punteggio: {self.punteggio:06d}", (0, 220, 255), centro=(500, 240))
        self._testo(self.font, "Inserisci le tue 3 iniziali", COLORE_TESTO, centro=(500, 270))

        for i, lettera in enumerate(self.nick):
            x = 500 + (i - 1) * 80
            attiva = i == self.nick_cursore
            colore = COLORE_BOOST if attiva else COLORE_TESTO
            self._testo(self.font_nick, lettera, colore, centro=(x, 345))
            pygame.draw.line(self.surface_virtuale, colore, (x - 28, 390), (x + 28, 390),
                             4 if attiva else 2)
            if attiva and (now // 300) % 2 == 0:
                pygame.draw.polygon(self.surface_virtuale, colore, [(x - 8, 402), (x + 8, 402), (x, 412)])

        self._testo(self.font, "Scrivi le lettere  o  usa SU/GIU e SINISTRA/DESTRA",
                    (170, 190, 210), centro=(500, 430))
        self._testo(self.font, "[BACKSPACE] indietro    [ENTER] conferma", COLORE_TESTO,
                    centro=(500, 458))

    def _disegna_istruzioni(self, now: int) -> None:
        self.surface_virtuale.fill((15, 30, 50))
        self._disegna_mare_pixel(now)
        self._testo(self.font_titolo, "THE PIRATINZ - COMANDI DI GIOCO",
                    COLORE_ORO, centro=(500, 60))

        y = 112
        for tasto, descrizione in COMANDI:
            for x, larghezza in ((40, 340), (390, 570)):
                box = pygame.Surface((larghezza, 48), pygame.SRCALPHA)
                box.fill((255, 255, 255, 20))
                self.surface_virtuale.blit(box, (x, y))
            self._testo(self.font_comando, tasto, COLORE_BOOST, topleft=(50, y + 16))
            self._testo(self.font, descrizione, COLORE_TESTO, topleft=(405, y + 15))
            y += 58

        self._testo(self.font_grande, "Premi [ENTER] per salpare!", (255, 255, 0),
                    centro=(500, 612))

    def _disegna_pausa(self) -> None:
        self._pannello(620, 360, 215)
        self._testo(self.font_titolo, "PAUSA", COLORE_ORO, centro=(500, 180))
        for i, voce in enumerate(OPZIONI_PAUSA):
            scelta = i == self.pausa_voce
            testo_voce = voce
            if i == 1:
                stato_crt = "ATTIVO" if self.filtro_crt_attivo else "DISATTIVO"
                testo_voce = f"Filtro CRT: {stato_crt}"

            self._testo(self.font_grande, f"> {testo_voce} <" if scelta else testo_voce,
                        COLORE_BOOST if scelta else COLORE_TESTO, centro=(500, 235 + i * 45))
        self._testo(self.font, "SU/GIU per scegliere  -  ENTER/SX/DX modifica  -  ESC riprende",
                    (170, 190, 210), centro=(500, 465))

    def _disegna_transizione(self, now: int) -> None:
        t = (now - self.transizione_inizio) / DURATA_TRANSIZIONE_MS
        if t >= 1.0 or self.snap is None:
            self.transizione_inizio = None
            self.snap = None
            return
        spinta = t ** 1.8
        alt = 50
        for i in range(ALTEZZA // alt + 1):
            y = i * alt
            h = min(alt, ALTEZZA - y)
            if h <= 0:
                break
            fattore = 1.05 + 0.25 * (0.5 + 0.5 * math.sin(i * 0.9 + t * 5))
            x = -spinta * LARGHEZZA * fattore
            dy = math.sin(i * 1.3 + t * 9) * 5 * t
            self.surface_virtuale.blit(self.snap, (int(x), int(y + dy)), pygame.Rect(0, y, LARGHEZZA, h))
            bordo = int(x + LARGHEZZA)
            if 0 < bordo < LARGHEZZA:
                ym = int(y + dy + h / 2)
                pygame.draw.line(self.surface_virtuale, (225, 240, 255), (bordo + 4, ym),
                                 (bordo + 4 + int(60 + 80 * t), ym), 2)

    def _disegna_record(self, now: int) -> None:
        t = (now - self.record_t0) / 1000
        s = self.surface_virtuale
        entrata = min(1.0, t / 0.35)

        self.velo.fill((0, 0, 0, int(175 * entrata)))
        centro = (500, 290)
        n = 18
        passo = 2 * math.pi / n
        for k in range(0, n, 2):
            a0 = t * 0.6 + k * passo
            a1 = a0 + passo
            pygame.draw.polygon(self.velo, (255, 215, 0, int(70 * entrata)), [
                centro,
                (centro[0] + 900 * math.cos(a0), centro[1] + 900 * math.sin(a0)),
                (centro[0] + 900 * math.cos(a1), centro[1] + 900 * math.sin(a1)),
            ])
        s.blit(self.velo, (0, 0))

        colori = [(255, 215, 0), (255, 69, 0), (0, 220, 255),
                  (255, 105, 180), (124, 252, 0), (255, 255, 255)]
        for j in range(70):
            x = (j * 137.5) % LARGHEZZA + math.sin(t * 3 + j) * 18
            y = ((t * (110 + (j * 53) % 120) + j * 91) % (ALTEZZA + 60)) - 30
            pygame.draw.rect(s, colori[j % len(colori)], (int(x), int(y), 8, 5 + j % 4))

        x = min(1.0, t / 0.6)
        scala = max(0.05, 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2)
        scala *= 1 + 0.05 * math.sin(t * 7)
        lampo = 0.5 + 0.5 * math.sin(t * 9)
        colore = (255, 215 + int(40 * lampo), 50 + int(150 * lampo))
        angolo = math.sin(t * 3) * 3
        for colore_testo, scarto in (((60, 20, 0), 5), (colore, 0)):
            testo = self.font_record.render("NUOVO RECORD!", True, colore_testo)
            ruotato = pygame.transform.rotozoom(testo, angolo, scala)
            s.blit(ruotato, ruotato.get_rect(center=(500 + scarto, 250 + scarto)))

        if t > 0.5:
            self._testo(self.font_grande, f"Punteggio: {self.punteggio:06d}", (0, 220, 255),
                        centro=(500, 340))
            posto = self.record_posto
            frase = ("PRIMO POSTO IN CLASSIFICA!" if posto == 0
                     else f"{posto + 1}° POSTO IN CLASSIFICA!")
            self._testo(self.font_classifica, frase, COLORE_ORO, centro=(500, 395))
        if now - self.record_t0 >= SKIP_RECORD_DOPO_MS and (now // 500) % 2 == 0:
            self._testo(self.font, "Premi un tasto per continuare", COLORE_TESTO,
                        centro=(500, 470))

    def _disegna_gioco(self, now: int) -> None:
        self._disegna_mare(now)
        self._disegna_fx_basso(now)
        self._disegna_mondo(now)
        self._disegna_barca(now)
        self._disegna_fx_alto()
        
        for tf in self.livello.testi_fluttuanti:
            self._testo_con_contorno(
                self.font_grande,
                tf["testo"],
                colore_testo=tf["colore"],
                colore_bordo=(255, 255, 255) if tf["colore"] == (255, 50, 50) else (0, 0, 0),
                centro=(int(tf["x"]), int(tf["y"]))
            )

        self._disegna_hud(now)

        if self.banner_frame > 0:
            alpha = min(255, self.banner_frame * 6)
            s_banner = self.font_banner.render(f"LIVELLO {self.numero_livello} - PRONTI!", True, COLORE_ORO)
            s_banner.set_alpha(alpha)
            rect_b = s_banner.get_rect(center=(500, 320))
            self.surface_virtuale.blit(s_banner, rect_b)

        self._disegna_esito(now)

    def _disegna_fx_basso(self, now: int) -> None:
        if not EFFETTI_ATTIVI:
            return
        lv = self.livello
        strato = self.strato_basso
        strato.fill((0, 0, 0, 0))

        for ostacoli, spessore, periodo in ((lv.isole, 14, 2600), (lv.scogli, 10, 1800)):
            for o in ostacoli:
                pygame.draw.circle(strato, (*ACQUA_CHIARA, 55), o.pos, o.raggio + spessore)
                for sfasamento in (0.0, 0.5):
                    t = (now / periodo + o.fase + sfasamento) % 1.0
                    raggio = o.raggio + 2 + t * (spessore + 6)
                    alpha = 55 + int(110 * (1 - t))
                    pygame.draw.circle(strato, (*SCHIUMA, alpha), o.pos, int(raggio), 2)

        lv.fx.disegna(strato, 0)
        self.surface_virtuale.blit(strato, (0, 0))

    def _disegna_fx_alto(self) -> None:
        fx = self.livello.fx
        if not EFFETTI_ATTIVI or not fx.contiene(1):
            return
        self.strato_alto.fill((0, 0, 0, 0))
        fx.disegna(self.strato_alto, 1)
        self.surface_virtuale.blit(self.strato_alto, (0, 0))

    def _disegna_mare(self, now: int) -> None:
        self.surface_virtuale.fill(COLORE_MARE)
        lv = self.livello
        v = lv.vento

        if lv.atmosfera.tinta_mare:
            surf_tinta = pygame.Surface((LARGHEZZA, ALTEZZA), pygame.SRCALPHA)
            surf_tinta.fill(lv.atmosfera.tinta_mare)
            self.surface_virtuale.blit(surf_tinta, (0, 0))

        rad = math.radians(v.angolo)
        lunghezza = 15 + v.forza * 8
        dx, dy = math.sin(rad) * lunghezza, -math.cos(rad) * lunghezza
        for px in range(50, LARGHEZZA, 150):
            for py in range(60, 600, 120):
                pygame.draw.line(self.surface_virtuale, COLORE_VENTO, (px, py), (px + dx, py + dy), 2)
                pygame.draw.circle(self.surface_virtuale, COLORE_VENTO, (int(px + dx), int(py + dy)), 3)

        for nuvola in lv.nuvole:
            self.surface_virtuale.blit(nuvola["surf"], (int(nuvola["x"] - nuvola["rx"]), int(nuvola["y"] - nuvola["ry"])))

        for g in lv.gocce_pioggia:
            pygame.draw.line(self.surface_virtuale, (180, 210, 240, 150), (g["x"], g["y"]), (g["x"] + 2, g["y"] + 8), 1)

        if lv.flash_fulmine_timer > 0:
            self.surface_virtuale.blit(self.flash_fulmine, (0, 0))

    def _disegna_mondo(self, now: int) -> None:
        lv = self.livello
        s = self.surface_virtuale

        pygame.draw.circle(s, COLORE_PORTO_A, lv.porto_a, 25, 4)
        self._testo(self.font, "PORTO A", COLORE_TESTO,
                    topleft=(lv.porto_a[0] - 30, lv.porto_a[1] + 32))

        bx, by = lv.porto_b
        pygame.draw.circle(s, COLORE_PORTO_B_LEGNO, (bx, by), RAGGIO_PORTO_B)
        pygame.draw.circle(s, COLORE_PORTO_B_BASE, (bx, by), RAGGIO_PORTO_B - 12)
        pygame.draw.circle(s, COLORE_ORO, (bx, by), 10)
        self._testo(self.font, "ARRIVO (B)", COLORE_TESTO, topleft=(bx - 42, by - 40))

        t_moneta = now / 200
        scala_x = abs(math.sin(t_moneta))
        for m in lv.monete:
            rx = max(2, int(m["raggio"] * scala_x))
            ry = m["raggio"]
            pygame.draw.ellipse(s, (255, 215, 0), (m["x"] - rx, m["y"] - ry, rx * 2, ry * 2))
            pygame.draw.ellipse(s, (218, 165, 32), (m["x"] - rx, m["y"] - ry, rx * 2, ry * 2), 2)

        for isola in lv.isole:
            pygame.draw.circle(s, COLORE_SABBIA, isola.pos, isola.raggio)
            pygame.draw.circle(s, COLORE_VERDE, isola.pos, isola.raggio - 12)

        for scoglio in lv.scogli:
            pygame.draw.circle(s, COLORE_SCOGLIO, scoglio.pos, scoglio.raggio)
            pygame.draw.circle(s, COLORE_BORDO_SCOGLIO, scoglio.pos, scoglio.raggio, 2)

        for barile in lv.barili:
            c = (int(barile.x), int(barile.y))
            if barile.rosso:
                pygame.draw.circle(s, COLORE_BARILE_ROSSO, c, barile.raggio)
                pygame.draw.circle(s, (100, 0, 0), c, barile.raggio, 2)
                pygame.draw.line(s, COLORE_TESTO, (c[0] - 6, c[1]), (c[0] + 6, c[1]), 3)
                pygame.draw.line(s, COLORE_TESTO, (c[0], c[1] - 6), (c[0], c[1] + 6), 3)
            else:
                pygame.draw.circle(s, COLORE_BARILE, c, barile.raggio)
                pygame.draw.circle(s, COLORE_CERCHIO_BARILE, c, barile.raggio, 2)
                pygame.draw.line(s, COLORE_CERCHIO_BARILE, (c[0] - 10, c[1]), (c[0] + 10, c[1]), 2)

    def _testo_con_contorno(self, font, testo, colore_testo, colore_bordo, centro) -> None:
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            s_bordo = font.render(testo, True, colore_bordo)
            rect_bordo = s_bordo.get_rect(center=(centro[0] + dx, centro[1] + dy))
            self.surface_virtuale.blit(s_bordo, rect_bordo)
        
        s_testo = font.render(testo, True, colore_testo)
        rect_testo = s_testo.get_rect(center=centro)
        self.surface_virtuale.blit(s_testo, rect_testo)

    def _disegna_barca(self, now: int) -> None:
        lv = self.livello
        b = lv.barca
        centro = (int(b.x), int(b.y))

        if lv.esito is Esito.DISTRUTTA:
            pygame.draw.circle(self.surface_virtuale, (255, 69, 0), centro, 25)
            pygame.draw.circle(self.surface_virtuale, COLORE_ORO, centro, 15)
            return

        lampeggio_spento = b.in_invulnerabilita(now) and (now // 100) % 2 != 0
        lampeggio_iniziale = lv.in_lampeggio_iniziale(now) and (now // 200) % 2 != 0
        if lampeggio_spento or lampeggio_iniziale or lv.esito is Esito.COMPLETATO:
            return

        if lv.boost_attivo(now):
            pygame.draw.circle(self.surface_virtuale, COLORE_BOOST, centro, 35, 2)

        for superficie, angolo in ((self.surf_scafo, b.angolo), (self.surf_vela, b.angolo_vela)):
            ruotata = pygame.transform.rotate(superficie, -angolo)
            self.surface_virtuale.blit(ruotata, ruotata.get_rect(center=centro))

    def _disegna_hud(self, now: int) -> None:
        lv = self.livello
        b, v = lv.barca, lv.vento
        s = self.surface_virtuale

        s.blit(self.barra_alto, (0, 0))
        colore = (255, 80, 80) if v.forza >= 5 else COLORE_TESTO

        testo = self.font.render(
            f"Vento: {v.nome} ({v.secondi_al_cambio(now)}s) | Forza:", True, colore)
        s.blit(testo, (15, 8))
        x = 15 + testo.get_width() + 5
        for i in range(6):
            pygame.draw.rect(s, colore if i < v.forza else COLORE_SPENTO,
                             (x + i * 10, 9, 8, 12))
        
        self._testo(self.font, f"Vel: {round(b.velocita, 1)}", COLORE_TESTO, topleft=(15, 28))

        punteggio_corrente = self.punteggio
        if lv.esito is Esito.IN_CORSO:
            punteggio_corrente += lv.punti

        t_score = self.font_arcade.render(f"SCORE:{punteggio_corrente:06d}", True, COLORE_TESTO)
        
        hi_corrente = max(self.classifica.high_score, punteggio_corrente)
        is_new_high = punteggio_corrente > self.classifica.high_score
        colore_hi = COLORE_ORO
        if is_new_high and (now // 200) % 2 == 0:
            colore_hi = (0, 255, 255)

        t_hi = self.font_arcade.render(f"HI:{hi_corrente:06d}", True, colore_hi)
        s.blit(t_score, (270, 8))
        s.blit(t_hi, (270, 28))
        
        self._testo(self.font, "Vite:", COLORE_TESTO, topleft=(520, 16))
        max_vite_visibili = max(3, b.vite)
        for i in range(max_vite_visibili):
            disegna_teschio_arcade(s, 560 + i * 20, 22, attivo=(i < b.vite))

        self._testo(self.font, "Boost:", COLORE_TESTO, topleft=(665, 16))
        for i in range(lv.cfg.pip_boost):
            c = (725 + i * 18, 24)
            pygame.draw.circle(s, COLORE_BOOST if i < lv.pip_boost else COLORE_SPENTO, c, 6)
            pygame.draw.circle(s, COLORE_TESTO, c, 6, 1)

        s.blit(self.cappello_hud, (945, 11))

        s.blit(self.barra_basso, (0, HUD_BASSO_Y))
        self._testo(self.font_grande, f"LIVELLO {lv.numero}/{LIVELLO_FINALE}",
                    COLORE_ORO, topleft=(30, 645))
        colore_timer = (255, 50, 50) if lv.secondi_rimanenti <= 5 else COLORE_TESTO
        self._testo(self.font_timer, f"00:{lv.secondi_rimanenti:02d}", colore_timer,
                    centro=(500, 660))

        centro = (930, 660)
        raggio = 28
        pygame.draw.circle(s, (10, 50, 120), centro, raggio)
        pygame.draw.circle(s, COLORE_TESTO, centro, raggio, 2)
        rad = math.radians(v.angolo)
        punta = (centro[0] + math.sin(rad) * (raggio - 8),
                 centro[1] - math.cos(rad) * (raggio - 8))
        pygame.draw.line(s, (255, 255, 0), centro, punta, 3)
        pygame.draw.circle(s, COLORE_TESTO, centro, 4)

    def _disegna_esito(self, now: int) -> None:
        lv = self.livello
        if lv.esito is Esito.IN_CORSO:
            return
        if self.record_attivo:
            if now >= self.record_t0:
                self._disegna_record(now)
            return
        if self.nick_attivo:
            self._disegna_inserimento_nick(now)
            return

        if lv.esito is Esito.COMPLETATO:
            self._pannello(720, 210, 220)
            self._testo(self.font_grande, "HAI COMPLETATO THE REAL PIRATE!",
                        COLORE_ORO, centro=(500, 270))
            self._testo(self.font, f"Punteggio Totale Finale: {self.punteggio:06d} punti",
                        (0, 220, 255), centro=(500, 310))
            self._testo(self.font, "Premi [ENTER] per tornare al Title Screen",
                        COLORE_TESTO, centro=(500, 350))
            self._testo(self.font, "Premi [L] per vedere la classifica",
                        (150, 220, 255), centro=(500, 380))

        elif lv.esito is Esito.SUPERATO:
            self._pannello(700, 160, 210)
            self._testo(self.font_grande, f"LIVELLO {lv.numero} SUPERATO!",
                        COLORE_ORO, centro=(500, 275))
            
            msg_bonus = ""
            if lv.danni_subiti == 0:
                msg_bonus += " [NO DANNI +200]"
            if lv.monete_raccolte_livello == lv.monete_totali_livello and lv.monete_totali_livello > 0:
                msg_bonus += " [MONETE PERFECT +300]"

            if msg_bonus:
                self._testo(self.font, f"BONUS PERFETTO:{msg_bonus}", (124, 252, 0), centro=(500, 305))

            self._testo(self.font, f"Punteggio Totale: {self.punteggio:06d}",
                        (0, 220, 255), centro=(500, 330))
            self._testo(self.font, "Premi [ENTER] per passare al livello successivo",
                        COLORE_TESTO, centro=(500, 360))

        else:
            self._pannello(600, 170, 210)
            titoli = {
                "tempo_scaduto": ("TEMPO SCADUTO!", (255, 120, 0)),
                "avaria": ("BARCA IN AVARIA!", (255, 120, 0)),
                "esplosione": ("BARCA ESPLOSA!", (255, 50, 50)),
            }
            titolo, colore = titoli.get(lv.motivo, titoli["esplosione"])
            self._testo(self.font_grande, titolo, colore, centro=(500, 280))
            self._testo(self.font, f"Punteggio Finale Raggiunto: {self.punteggio:06d}",
                        (0, 220, 255), centro=(500, 315))
            self._testo(self.font, "Premi [ENTER] per ricominciare dal Livello 1",
                        COLORE_TESTO, centro=(500, 350))
            self._testo(self.font, "Premi [L] per vedere la classifica",
                        (150, 220, 255), centro=(500, 380))


def main() -> None:
    Gioco().esegui()
    sys.exit()


if __name__ == "__main__":
    main()
