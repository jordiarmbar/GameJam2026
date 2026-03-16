import pygame
import random
import os
import sys
import math
from collections import Counter

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Carta:
    PALOS = {"♠": "Picas", "♥": "Corazones", "♦": "Diamantes", "♣": "Tréboles"}
    NOMBRES = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
               10:"10",11:"J",12:"Q",13:"K",14:"A"}
    COLOR_PALOS = {"♠": (40,40,40), "♣": (40,40,40), "♥": (210,50,50), "♦": (210,50,50)}

    def __init__(self, palo: str, valor_base: int, rondas_sobrevividas: int = 0):
        self.palo = palo
        self.nombre_palo = self.PALOS[palo]
        self.color = self.COLOR_PALOS[palo]
        self.valor_base = valor_base
        self.rondas_sobrevividas = rondas_sobrevividas
        self.fichas = self._calcular_fichas()

        self.selected = False
        self.hover = False
        self.rect = pygame.Rect(0, 0, 100, 150)

    def _calcular_fichas(self) -> int:
        base = 30 
        if self.valor_base == 14: return base + 11
        elif self.valor_base >= 11: return base + 10
        else: return base + self.valor_base

    @property
    def precio_venta(self) -> int:
        return self.rondas_sobrevividas * 100

    def evolucionar(self):
        if self.valor_base < 14:
            self.valor_base += 1
        self.rondas_sobrevividas += 1
        self.fichas = self._calcular_fichas()

    @property
    def nombre(self) -> str:
        return f"{self.NOMBRES.get(self.valor_base, str(self.valor_base))}"

    @property
    def es_as(self) -> bool:
        return self.valor_base == 14

class Mazo:
    def __init__(self):
        valores_frecuentes = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        self.cartas = []
        for _ in range(52):
            palo = random.choice(list(Carta.PALOS.keys()))
            valor = random.choice(valores_frecuentes)
            self.cartas.append(Carta(palo, valor))
            
        random.shuffle(self.cartas)

    def robar(self, n: int):
        n = min(n, len(self.cartas))
        robadas = self.cartas[:n]
        self.cartas = self.cartas[n:]
        return robadas

    def devolver(self, cartas):
        for c in cartas:
            c.selected = False 
        random.shuffle(cartas)
        self.cartas.extend(cartas)

    def anadir(self, carta):
        pos = random.randint(0, len(self.cartas))
        self.cartas.insert(pos, carta)

    def evolucionar_todas(self):
        for c in self.cartas:
            c.evolucionar()

    def añadir_gratuitas(self, cantidad=3):
        for _ in range(cantidad):
            self.anadir(Carta(random.choice(list(Carta.PALOS.keys())), 2, 0))

    def destruir_ases(self):
        ases = [c for c in self.cartas if c.es_as]
        self.cartas = [c for c in self.cartas if not c.es_as]
        return len(ases)

    def is_empty(self):
        return len(self.cartas) == 0

TABLA_MANOS = {
    "Color": (35, 4), "Full House": (40, 4), "Trío": (30, 3),
    "Doble Pareja": (20, 2), "Pareja": (10, 2), "Carta Alta": (5, 1)
}

def evaluar_mano(cartas):
    if not cartas: return "Carta Alta", *TABLA_MANOS["Carta Alta"]
    palos = [c.palo for c in cartas]
    frec = sorted(Counter(c.valor_base for c in cartas).values(), reverse=True)
    
    if len(set(palos)) == 1 and len(cartas) >= 3: return "Color", *TABLA_MANOS["Color"]
    if frec[0] == 3 and len(frec) > 1 and frec[1] == 2: return "Full House", *TABLA_MANOS["Full House"]
    if frec[0] >= 3: return "Trío", *TABLA_MANOS["Trío"]
    if frec.count(2) >= 2: return "Doble Pareja", *TABLA_MANOS["Doble Pareja"]
    if frec[0] == 2: return "Pareja", *TABLA_MANOS["Pareja"]
    return "Carta Alta", *TABLA_MANOS["Carta Alta"]

def calcular_puntos(cartas_jugadas, jokers):
    tipo, fbase, mult = evaluar_mano(cartas_jugadas)
    fichas_cartas = sum(c.fichas for c in cartas_jugadas)
    
    bonus_fichas, mult_extra = 0, 1.0
    for j in jokers:
        bf, me = j.bonus_puntuacion(tipo, cartas_jugadas)
        bonus_fichas += bf
        mult_extra *= me

    total_fichas = fichas_cartas + fbase + bonus_fichas
    total_mult = mult * mult_extra
    return int(total_fichas * total_mult), f"{tipo} ({total_fichas} f × {total_mult:.1f})"

class Joker:
    nombre = "Base"
    desc = ""
    emoji = "🃏"
    def bonus_puntuacion(self, t, cs): return 0, 1.0
    def bonus_venta(self, c): return 0

class J_CampeonMult(Joker): nombre, desc, emoji = "El Campeón", "×1.5 mult global", "🏆"; bonus_puntuacion = lambda s,t,cs: (0, 1.5)
class J_FichasExtra(Joker): nombre, desc, emoji = "El Coleccionista", "+20 fichas global", "💎"; bonus_puntuacion = lambda s,t,cs: (20, 1.0)
class J_Parejas(Joker): nombre, desc, emoji = "El Gemelo", "×2 mult Parejas", "👥"; bonus_puntuacion = lambda s,t,cs: (0, 2.0) if t in ("Pareja","Doble Pareja") else (0, 1.0)
class J_Venta300(Joker): nombre, desc, emoji = "El Anticuario", "+300 pts al vender", "🏺"; bonus_venta = lambda s,c: 300
class J_Solitario(Joker): nombre, desc, emoji = "El Solitario", "Carta Alta ×4", "🧙"; bonus_puntuacion = lambda s,t,cs: (0, 4.0) if t=="Carta Alta" else (0, 1.0)
POOL_JOKERS = [J_CampeonMult, J_FichasExtra, J_Parejas, J_Venta300, J_Solitario]

pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.SCALED)
pygame.display.set_caption("TCG Space")

icon_path = resource_path(os.path.join("context", "icon.ico"))
if os.path.exists(icon_path):
    icon_surf = pygame.image.load(icon_path)
    pygame.display.set_icon(icon_surf)

clock = pygame.time.Clock()

BG_COLOR = (24, 33, 41)
PANEL_COLOR = (36, 48, 60)
TEXT_COLOR = (230, 235, 240)
HIGHLIGHT_COLOR = (255, 215, 0)
GREEN = (70, 200, 100)
RED = (220, 70, 70)

font_small = pygame.font.SysFont("segoeuisymbol", 18)
font_med = pygame.font.SysFont("segoeuisymbol", 28)
font_large = pygame.font.SysFont("segoeuisymbol", 48)

class Button:
    def __init__(self, text, x, y, w, h, color=PANEL_COLOR):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover = False

    def draw(self, surface):
        c = (min(self.color[0]+30, 255), min(self.color[1]+30, 255), min(self.color[2]+30, 255)) if self.hover else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=8)
        pygame.draw.rect(surface, (100, 110, 120), self.rect, 2, border_radius=8)
        
        txt_surf = font_med.render(self.text, True, TEXT_COLOR)
        surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        self.hover = self.rect.collidepoint(pos)
        return self.hover

def draw_card(surface, carta: Carta, x, y, hover=False, selected=False, frame_count=0):
    pulse = 0
    if not selected:
        pulse = int(math.sin(frame_count * 0.1) * 3)
    
    rect = pygame.Rect(x - pulse//2, y - (15 if hover or selected else 0) - pulse//2, 120 + pulse, 180 + pulse)
    carta.rect = rect
    
    if selected:
        pygame.draw.rect(surface, HIGHLIGHT_COLOR, rect.inflate(12,12), border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255), rect.inflate(6,6), 2, border_radius=10)
    
    color_base = (255, 255, 255) if not hover else (240, 245, 255)
    pygame.draw.rect(surface, color_base, rect, border_radius=8)
    pygame.draw.rect(surface, (180, 190, 200), rect, 2, border_radius=8)
    
    color = carta.color
    r_font = font_large.render(carta.nombre, True, color)
    s_font = font_large.render(carta.palo, True, color)
    
    surface.blit(r_font, (rect.x + 8, rect.y + 4))
    surface.blit(s_font, (rect.x + 8, rect.y + 45))

    pygame.draw.line(surface, (230, 230, 230), (rect.x + 5, rect.bottom - 55), (rect.right - 5, rect.bottom - 55), 1)
    
    f_txt = font_small.render(f"+{carta.fichas} F", True, (0,100,200))
    surface.blit(f_txt, (rect.x + 10, rect.bottom - 45))
    
    val = carta.precio_venta
    v_txt = font_small.render(f"v: {val}p" if val>0 else "v: 0", True, (200,100,0))
    surface.blit(v_txt, (rect.x + 10, rect.bottom - 25))

class FloatingText:
    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 60
        self.alpha = 255
        
    def update(self):
        self.y -= 2
        self.life -= 1
        self.alpha = max(0, int((self.life / 60) * 255))
        
    def draw(self, surface):
        if self.life > 0:
            txt = font_med.render(self.text, True, self.color)
            txt.set_alpha(self.alpha)
            surface.blit(txt, (self.x, self.y))

class GameEngine:
    def __init__(self):
        self.state = "START"
        self.mazo = Mazo()
        self.mano = []
        self.jokers = []
        self.floating_texts = []
        
        self.nivel = 1
        self.ronda = 1
        self.puntos = 0
        self.turnos = 5
        self.objetivo = 400
        
        self.btn_play = Button("Jugar Mano", WIDTH//2 - 250, HEIGHT - 80, 200, 50, GREEN)
        self.btn_sell = Button("Vender", WIDTH//2 - 30, HEIGHT - 80, 120, 50, RED)
        self.btn_shop = Button("Tienda [🛒]", WIDTH//2 + 110, HEIGHT - 80, 180, 50)
        self.btn_next = Button("Continuar", WIDTH//2 - 100, HEIGHT - 120, 200, 60, GREEN)
        
        self.shop_items = [(2, 60), (4, 120), (7, 250)]
        self.shop_btns = []
        
        self.joker_options = []
        self.joker_btns = []

        self.last_play_info = ""
        self.total_turns_played = 0
        self.current_planet_scale = 1.0
        self.last_planet_idx = 0
        self.frame_count = 0

        self.level_backgrounds = []
        self.planet_animations = []
        try:
            bg_files = ["Space Background (1).png", "Space Background (2).png", "Space Background (3).png", "Space Background.png"]
            for f in bg_files:
                path = resource_path(os.path.join("context", f))
                if os.path.exists(path):
                    self.level_backgrounds.append(pygame.transform.scale(pygame.image.load(path).convert(), (WIDTH, HEIGHT)))
                else:
                    self.level_backgrounds.append(None)
            
            self.planet_animations = []
            assets = ["earth_sprite.png", "moon_sprite.png", "mars_sprite.png", "blackhole_sprite.png"]
            for asset in assets:
                p_path = resource_path(os.path.join("context", asset))
                if os.path.exists(p_path):
                    if "sprite.png" in asset:
                        img = pygame.image.load(p_path).convert_alpha()
                        w, h = img.get_size() 
                        frames = []
                        for x in range(0, w, h):
                            frame = pygame.transform.scale(img.subsurface((x, 0, h, h)), (200, 200))
                            frames.append(frame)
                        self.planet_animations.append(frames)
                    else:
                        img = pygame.image.load(p_path).convert_alpha()
                        frame = pygame.transform.scale(img, (200, 200))
                        self.planet_animations.append([frame]) 
            self.planet_anim_idx = 0.0
            
            self.galaxy_frames = []
            self.galaxy_anim_idx = 0.0
            g_path = resource_path(os.path.join("context", "galaxy_green.png"))
            if os.path.exists(g_path):
                img = pygame.image.load(g_path).convert_alpha()
                w, h = img.get_size()
                for x in range(0, w, h): 
                    frame = img.subsurface((x, 0, h, h))
                    self.galaxy_frames.append(pygame.transform.scale(frame, (250, 250))) 
            
            self.setup_map()
            
        except Exception as e:
            print(f"Error cargando assets: {e}")

    def setup_map(self):
        self.state = "MAP"
        self.map_btns = []
        spacing = WIDTH // 5
        for i in range(4):
            x = spacing * (i + 1)
            y = HEIGHT // 2
            r = pygame.Rect(x - 50, y - 50, 100, 100)
            self.map_btns.append((r, i))
            
    def init_shop_btns(self):
        self.shop_btns = []
        for i in range(2, 15):
            rank_idx = i - 2
            row = rank_idx // 7
            col = rank_idx % 7
            
            cost = i * 30
            name = Carta.NOMBRES.get(i, str(i))
            
            w, h = 135, 50
            margin = 15
            grid_w = (7 * w) + (6 * margin)
            start_x = WIDTH // 2 - grid_w // 2
            start_y = HEIGHT // 2 - 80
            
            btn = Button(f"{name} ({cost}p)", start_x + col * (w + margin), start_y + row * (h + margin), w, h)
            self.shop_btns.append((btn, i, cost))
            
        self.btn_close_shop = Button("Volver", WIDTH//2 - 100, HEIGHT - 80, 200, 50)

    def start_round(self):
        self.turnos = 5
        self.objetivo = int(400 * (2.0**(self.nivel-1)) * (1.5**(self.ronda-1)))
        if self.ronda == 3: self.objetivo = int(self.objetivo * 2.2) 
        
        self.mazo.añadir_gratuitas(3)
        self.mano = []
        self.fill_hand()
        self.state = "PLAYING"
        self.last_play_info = f"¡Empezando Nivel {self.nivel} - Ronda {self.ronda}!"

    def fill_hand(self):
        faltan = 8 - len(self.mano)
        if faltan > 0 and not self.mazo.is_empty():
            self.mano.extend(self.mazo.robar(faltan))

    def update_hand_layout(self):
        start_x = WIDTH//2 - (len(self.mano)*130)//2
        for i, c in enumerate(self.mano):
            c.rect.x = start_x + i*130
            c.rect.y = HEIGHT - 300

    def play_selected(self):
        selected = [c for c in self.mano if c.selected]
        if not selected: return
        
        pts, desc = calcular_puntos(selected, self.jokers)
        self.puntos += pts
        self.turnos -= 1
        self.total_turns_played += 1
        
        self.floating_texts.append(FloatingText(f"+{pts} PUNTOS", WIDTH//2 - 50, HEIGHT//2, GREEN))
        self.last_play_info = f"Jugada: {desc} -> +{pts} puntos!"
        
        for c in selected: self.mano.remove(c)
        self.mazo.devolver(selected)
        
        self.check_round_end()
        self.fill_hand()
        self.check_deck_state()

    def sell_selected(self):
        selected = [c for c in self.mano if c.selected]
        if not selected: return
        
        total = 0
        for c in selected:
            val = c.precio_venta
            for j in self.jokers:
                val += j.bonus_venta(c)
            total += val
            self.floating_texts.append(FloatingText(f"+{val}p", c.rect.centerx, c.rect.y, HIGHLIGHT_COLOR))
            self.mano.remove(c)
            
        self.puntos += total
        self.last_play_info = f"Vendiste {len(selected)} cartas por {total} pts."
        self.fill_hand()
        self.check_deck_state()

    def check_deck_state(self):
        if len(self.mano) == 0 and self.mazo.is_empty():
            min_cost = min((cost for _, cost in self.shop_items), default=0)
            if self.puntos < min_cost:
                self.state = "GAME_OVER"
                self.last_play_info = "Bancarrota: No te quedan cartas ni puntos."
            else:
                self.state = "NEED_CARDS"

    def check_round_end(self):
        if self.puntos >= self.objetivo:
            if self.nivel == 4 and self.ronda == 3:
                self.state = "VICTORY"
            else:
                self.state = "ROUND_WON"
        elif self.turnos <= 0:
            self.state = "GAME_OVER"

    def handle_events(self):
        pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_F11, pygame.K_f):
                    pygame.display.toggle_fullscreen()
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "PLAYING":
                    for c in reversed(self.mano): 
                        if c.rect.collidepoint(pos):
                            c.selected = not c.selected
                            break
                    if self.btn_play.check_hover(pos): self.play_selected()
                    elif self.btn_sell.check_hover(pos): self.sell_selected()
                    elif self.btn_shop.check_hover(pos): 
                        self.init_shop_btns()
                        self.state = "SHOP"
                
                elif self.state == "ROUND_WON":
                    if self.btn_next.check_hover(pos):
                        self.post_round_logic()
                
                elif self.state == "MAP":
                    for r, idx in self.map_btns:
                        if r.collidepoint(pos) and idx == self.nivel - 1:
                            self.start_round()
                
                elif self.state == "LEVEL_TRANSITION":
                    if self.btn_next.check_hover(pos):
                        self.setup_joker_selection()
                
                elif self.state == "JOKER_SEL":
                    for btn, j_cls in self.joker_btns:
                        if btn.check_hover(pos):
                            self.jokers.append(j_cls())
                            self.setup_map()
                            break
                    if self.btn_next.check_hover(pos): 
                        self.setup_map()

                elif self.state == "SHOP":
                    for btn, val, cost in self.shop_btns:
                        if btn.check_hover(pos) and self.puntos >= cost:
                            self.puntos -= cost
                            n = Carta(random.choice(list(Carta.PALOS.keys())), val, 0)
                            self.mazo.anadir(n)
                            self.floating_texts.append(FloatingText(f"+1 CARTA ({val})", btn.rect.centerx - 50, btn.rect.y - 30, GREEN))
                            if len(self.mano) < 8: self.mano.append(n)
                            self.last_play_info = f"🛒 Compraste un {val} por {cost}p"
                            break
                    if self.btn_close_shop.check_hover(pos):
                        if len(self.mano) == 0 and self.mazo.is_empty():
                            self.check_deck_state()
                        else:
                            self.state = "PLAYING"

                elif self.state == "START":
                    if self.btn_next.check_hover(pos):
                        self.setup_map()

                elif self.state == "NEED_CARDS":
                    if self.btn_shop.check_hover(pos):
                        self.init_shop_btns()
                        self.state = "SHOP"
                
                elif self.state in ("GAME_OVER", "VICTORY"):
                    if self.btn_next.check_hover(pos):
                        pygame.quit()
                        sys.exit()

        if self.state == "PLAYING":
            self.btn_play.check_hover(pos)
            self.btn_sell.check_hover(pos)
            self.btn_shop.check_hover(pos)
            for c in self.mano: c.hover = c.rect.collidepoint(pos)
        elif self.state in ("START", "ROUND_WON", "LEVEL_TRANSITION", "JOKER_SEL", "GAME_OVER", "VICTORY"):
            self.btn_next.check_hover(pos)
            if self.state == "JOKER_SEL":
                for b, _ in self.joker_btns: b.check_hover(pos)
        elif self.state == "SHOP":
            self.btn_close_shop.check_hover(pos)
            for b,_,_ in self.shop_btns: b.check_hover(pos)
        elif self.state == "NEED_CARDS":
            self.btn_shop.check_hover(pos)
            
        return True

    def post_round_logic(self):
        self.puntos -= self.objetivo
        
        self.mazo.devolver(self.mano)
        self.mano = []
        self.mazo.evolucionar_todas()
        
        if self.ronda == 3:
            d = self.mazo.destruir_ases()
            self.last_play_info = f"¡Planeta Completado! {d} Ases destruidos."
            self.nivel += 1
            self.ronda = 1
            self.state = "LEVEL_TRANSITION"
        else:
            self.ronda += 1
            self.last_play_info = "Ronda superada. ¡Acercándonos!"
            self.setup_joker_selection()

    def setup_joker_selection(self):
        if len(self.jokers) < 5:
            avails = [c for c in POOL_JOKERS if c not in [type(x) for x in self.jokers]]
            if avails:
                opts = random.sample(avails, min(3, len(avails)))
                self.joker_btns = []
                for i, j_cls in enumerate(opts):
                    btn = Button(f"{j_cls.nombre} {j_cls.emoji}", WIDTH//2 - 250, HEIGHT//2 - 50 + (i*70), 500, 50)
                    self.joker_btns.append((btn, j_cls))
                self.btn_next.text = "Saltar Comodín"
                self.btn_next.rect.y = HEIGHT - 100
                self.state = "JOKER_SEL"
                return
        
        self.setup_map()

    def draw(self, surface):
        self.frame_count += 1
        
        bg_idx = min(self.nivel - 1, len(self.level_backgrounds) - 1)
        if 0 <= bg_idx < len(self.level_backgrounds) and self.level_backgrounds[bg_idx]:
            surface.blit(self.level_backgrounds[bg_idx], (0, 0))
        else:
            surface.fill(BG_COLOR)
        
        if self.state == "START" and getattr(self, "galaxy_frames", []):
            self.galaxy_anim_idx += 0.08 
            if self.galaxy_anim_idx >= len(self.galaxy_frames):
                self.galaxy_anim_idx = 0
            
            frame = self.galaxy_frames[int(self.galaxy_anim_idx)]
            new_w, new_h = frame.get_size()
            surface.blit(frame, (WIDTH//2 - new_w//2, HEIGHT//2 - new_h//2 - 190))
            
        elif self.planet_animations:
            planet_idx = min(self.nivel - 1, 3) 
            
            frames = self.planet_animations[planet_idx]
            self.planet_anim_idx += 0.10 
            if self.planet_anim_idx >= len(frames):
                self.planet_anim_idx = 0
            
            base_scale = 1.0 + (self.ronda - 1) * 0.4
            turnos_jugados_ronda = 5 - self.turnos
            self.current_planet_scale = base_scale + (turnos_jugados_ronda * 0.05)
            
            base_img = frames[int(self.planet_anim_idx)]
            new_w = int(200 * self.current_planet_scale)
            new_h = int(200 * self.current_planet_scale)
            scaled_img = pygame.transform.scale(base_img, (new_w, new_h))
            
            surface.blit(scaled_img, (WIDTH//2 - new_w//2, HEIGHT//2 - new_h//2 - 180))
        
        pygame.draw.rect(surface, (40, 55, 75, 180), (0, 0, WIDTH, 85))
        pygame.draw.rect(surface, (100, 150, 255), (0, 85, WIDTH, 3)) 
        
        t1 = font_med.render(f"Nivel {self.nivel}   |   Ronda {'BOSS' if self.ronda==3 else self.ronda}", True, TEXT_COLOR)
        t2 = font_large.render(f"PUNTOS: {self.puntos} / {self.objetivo}", True, HIGHLIGHT_COLOR)
        t3 = font_med.render(f"Turnos: {self.turnos}/5", True, TEXT_COLOR)
        
        surface.blit(t1, (20, 25))
        t2_shadow = font_large.render(f"PUNTOS: {self.puntos} / {self.objetivo}", True, (20, 20, 20))
        surface.blit(t2_shadow, (WIDTH//2 - t2.get_width()//2 + 2, 12))
        surface.blit(t2, (WIDTH//2 - t2.get_width()//2, 10))
        surface.blit(t3, (WIDTH - 150, 25))
        
        for i, j in enumerate(self.jokers):
            jt = font_med.render(f"{j.emoji} {j.nombre}", True, (200,200,250))
            surface.blit(jt, (20, 100 + (i*40)))
            
        if self.state == "PLAYING" or (self.state == "ROUND_WON" and self.last_play_info):
            info_t = font_med.render(self.last_play_info, True, (255, 255, 200))
            surface.blit(info_t, (WIDTH//2 - info_t.get_width()//2, HEIGHT - 350))

        if self.state == "PLAYING":
            self.update_hand_layout()
            for c in self.mano: 
                if not c.selected: draw_card(surface, c, c.rect.x, c.rect.y, c.hover, False, self.frame_count)
            for c in self.mano: 
                if c.selected: draw_card(surface, c, c.rect.x, c.rect.y, c.hover, True, self.frame_count)
                
            self.btn_play.draw(surface)
            self.btn_sell.draw(surface)
            self.btn_shop.draw(surface)
            
            sel = [c for c in self.mano if c.selected]
            if sel:
                tipo, _, _ = evaluar_mano(sel)
                tt = font_med.render(f"Mano actual: {tipo}", True, TEXT_COLOR)
                surface.blit(tt, (WIDTH//2 - tt.get_width()//2, HEIGHT - 120))
                
        elif self.state == "ROUND_WON":
            win_t = font_large.render("¡RONDA SUPERADA!", True, GREEN)
            surface.blit(win_t, (WIDTH//2 - win_t.get_width()//2, HEIGHT//2 - 100))
            rem_t = font_med.render(f"Puntos restantes para el viaje: {self.puntos}", True, TEXT_COLOR)
            surface.blit(rem_t, (WIDTH//2 - rem_t.get_width()//2, HEIGHT//2 - 30))
            
            self.btn_next.text = "Continuar"
            self.btn_next.rect.y = HEIGHT - 150
            self.btn_next.draw(surface)

        elif self.state == "LEVEL_TRANSITION":
            tit = font_large.render("¡VIAJE INTERPLANETARIO!", True, HIGHLIGHT_COLOR)
            sub = font_med.render(self.last_play_info, True, TEXT_COLOR)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, HEIGHT//2 - 100))
            surface.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 - 30))
            
            self.btn_next.text = "Continuar viaje"
            self.btn_next.rect.y = HEIGHT - 150
            self.btn_next.draw(surface)
            
        elif self.state == "JOKER_SEL":
            tit = font_large.render("ELIGE UN COMODÍN PARA TU MAZO", True, HIGHLIGHT_COLOR)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, HEIGHT//8))
            for b, jcls in self.joker_btns:
                b.draw(surface)
                dt = font_small.render(jcls.desc, True, (150,150,150))
                surface.blit(dt, (b.rect.right + 20, b.rect.centery - 10))
            self.btn_next.text = "Saltar Comodín"
            self.btn_next.rect.y = HEIGHT - 100
            self.btn_next.draw(surface)
            
        elif self.state == "SHOP":
            tit = font_large.render("TIENDA DE CARTAS", True, TEXT_COLOR)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, HEIGHT//8))
            sub = font_med.render("Cualquier rango · Precio dinámico", True, (180, 180, 180))
            surface.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//8 + 60))

            for b, _, cost in self.shop_btns:
                b.color = (50, 150, 50) if self.puntos >= cost else (80, 80, 80)
                b.draw(surface)
            self.btn_close_shop.rect.y = HEIGHT - 100
            self.btn_close_shop.draw(surface)

        elif self.state == "START":
            tit = font_large.render("TCG SPACE", True, HIGHLIGHT_COLOR)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, HEIGHT//2 - 10))
            self.btn_next.text = "EMPEZAR"
            self.btn_next.rect.y = HEIGHT - 150
            self.btn_next.draw(surface)
            
            hint = font_small.render("Pulsa F11 o 'F' para alternar Pantalla Completa", True, (150, 150, 150))
            surface.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 30))
            
        elif self.state == "MAP":
            tit = font_large.render("MAPA ESTELAR", True, HIGHLIGHT_COLOR)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, 50))
            
            spacing = WIDTH // 5
            pygame.draw.line(surface, (100, 100, 100), (spacing, HEIGHT//2), (spacing*4, HEIGHT//2), 5)
            
            nombres = ["Tierra (Nv. 1)", "Luna (Nv. 2)", "Marte (Nv. 3)", "Agujero Negro"]
            for r, idx in self.map_btns:
                frames = self.planet_animations[idx]
                self.planet_anim_idx += 0.02 
                if self.planet_anim_idx >= len(frames): self.planet_anim_idx = 0
                frame = pygame.transform.scale(frames[int(self.planet_anim_idx) % len(frames)], (100, 100))
                
                if idx < self.nivel - 1:
                    frame.set_alpha(100)
                    surface.blit(frame, (r.x, r.y))
                    pygame.draw.circle(surface, GREEN, r.center, 55, 3)
                elif idx == self.nivel - 1:
                    frame.set_alpha(255)
                    size = 120 if r.collidepoint(pygame.mouse.get_pos()) else 100
                    p_img = pygame.transform.scale(frame, (size, size))
                    surface.blit(p_img, (r.centerx - size//2, r.centery - size//2))
                    pygame.draw.circle(surface, HIGHLIGHT_COLOR, r.center, size//2 + 5, 3)
                    
                    info = font_med.render("HAZ CLIC PARA ENTRAR", True, HIGHLIGHT_COLOR)
                    surface.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT - 150))
                else:
                    frame.set_alpha(50)
                    surface.blit(frame, (r.x, r.y))
                    
                nt = font_small.render(nombres[idx], True, TEXT_COLOR)
                surface.blit(nt, (r.centerx - nt.get_width()//2, r.bottom + 20))
                
        elif self.state == "NEED_CARDS":
            tit = font_large.render("¡TE HAS QUEDADO SIN CARTAS!", True, RED)
            sub = font_med.render("No puedes continuar. Compra cartas en la tienda para sobrevivir.", True, TEXT_COLOR)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, HEIGHT//2 - 50))
            surface.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 10))
            
            self.btn_shop.rect.x = WIDTH//2 - 100
            self.btn_shop.rect.y = HEIGHT - 150
            self.btn_shop.rect.w = 200
            self.btn_shop.draw(surface)

        elif self.state == "VICTORY":
            tit = font_large.render("¡HAS SALVADO LA GALAXIA!", True, HIGHLIGHT_COLOR)
            sub = font_med.render("Has derrotado al Agujero Negro. Eres una leyenda de Balatron.", True, TEXT_COLOR)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, HEIGHT//2 - 50))
            surface.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 10))
            self.btn_next.text = "Terminar Juego"
            self.btn_next.rect.y = HEIGHT - 150
            self.btn_next.draw(surface)
            
        elif self.state == "GAME_OVER":
            tit = font_large.render("GAME OVER", True, RED)
            surface.blit(tit, (WIDTH//2 - tit.get_width()//2, HEIGHT//2 - 30))
            self.btn_next.text = "Salir"
            self.btn_next.rect.y = HEIGHT - 150
            self.btn_next.draw(surface)

        for ft in self.floating_texts[:]:
            ft.update()
            if ft.life <= 0:
                self.floating_texts.remove(ft)
            else:
                ft.draw(surface)

if __name__ == "__main__":
    engine = GameEngine()
    running = True
    
    while running:
        running = engine.handle_events()
        engine.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()