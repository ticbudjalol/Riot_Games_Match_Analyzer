import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import os
import threading
import queue
import json

API_KEY = 'YOUR API HERE'

gui_queue = queue.Queue()
images = {}
match_frames = []
item_data = {}
item_images = {}
champ_images = {}

def nalozi_item_data():
    global item_data
    items_json_path = os.path.join('TrueGameData', 'Items.json')
    try:
        with open(items_json_path, 'r', encoding='utf-8') as f:
            item_list = json.load(f)
            item_data = {item['id']: item for item in item_list}
    except Exception as e:
        print(f"Napaka pri nalaganju Items.json: {e}")

def pridobi_vse():
    threading.Thread(target=_pridobi_vse).start()

def _pridobi_vse():
    try:
        ime = vnos_ime.get()
        GameTag = vnos_GameTag.get()
        if not ime or not GameTag:
            gui_queue.put(('Sporočilo', 'Prosimo, vnesite Riot ID in gameTag.'))
            return
        url = f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{ime}/{GameTag}?api_key={API_KEY}'
        response = requests.get(url)
        response.raise_for_status()
        podatki = response.json()
        puuid = podatki.get('puuid', 'Ni podatka')
        if puuid == 'Ni podatka':
            gui_queue.put(('Sporočilo', 'PUUID ni bilo mogoče pridobiti.'))
            return
        gameName = podatki.get('gameName', 'Ni podatka')
        tagLine = podatki.get('tagLine', 'Ni podatka')

        summoner_url = f"https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={API_KEY}"
        summoner_response = requests.get(summoner_url)
        summoner_response.raise_for_status()
        summoner_data = summoner_response.json()
        summoner_id = summoner_data.get('id', 'Ni podatka')
        summoner_name = summoner_data.get('name', 'Ni podatka')
        summoner_level = summoner_data.get('summonerLevel', 'Ni podatka')

        league_url = f"https://eun1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={API_KEY}"
        league_response = requests.get(league_url)
        league_response.raise_for_status()
        league_data = league_response.json()

        rankedSoloTier = rankedSoloRank = rankedSoloLP = rankedSoloWins = rankedSoloLosses = 'Ni podatka'
        rankedFlexTier = rankedFlexRank = rankedFlexLP = rankedFlexWins = rankedFlexLosses = 'Ni podatka'

        for entry in league_data:
            if entry['queueType'] == 'RANKED_SOLO_5x5':
                rankedSoloTier = entry['tier']
                rankedSoloRank = entry['rank']
                rankedSoloLP = entry['leaguePoints']
                rankedSoloWins = entry['wins']
                rankedSoloLosses = entry['losses']
            if entry['queueType'] == 'RANKED_FLEX_SR':
                rankedFlexTier = entry['tier']
                rankedFlexRank = entry['rank']
                rankedFlexLP = entry['leaguePoints']
                rankedFlexWins = entry['wins']
                rankedFlexLosses = entry['losses']

        gui_queue.put(('SummonerPodatki', {
            'summonerName': summoner_name,
            'summonerLevel': summoner_level,
            'rankedSoloTier': rankedSoloTier,
            'rankedSoloRank': rankedSoloRank,
            'rankedSoloLP': rankedSoloLP,
            'rankedSoloWins': rankedSoloWins,
            'rankedSoloLosses': rankedSoloLosses,
            'rankedFlexTier': rankedFlexTier,
            'rankedFlexRank': rankedFlexRank,
            'rankedFlexLP': rankedFlexLP,
            'rankedFlexWins': rankedFlexWins,
            'rankedFlexLosses': rankedFlexLosses
        }))

        gui_queue.put(('Sporočilo', f'PUUID: {puuid}\nIme: {gameName}\nTag: {tagLine}'))

        url = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=20&api_key={API_KEY}'
        response = requests.get(url)
        response.raise_for_status()
        match_ids = response.json()
        if not match_ids:
            gui_queue.put(('Sporočilo', 'Ni bilo mogoče pridobiti tekem.'))
            return
        gui_queue.put(('Sporočilo', 'Zadnjih 20 tekem pridobljenih.'))
        podrobnosti = []
        for i, match_id in enumerate(match_ids):
            url = f'https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}'
            response = requests.get(url)
            response.raise_for_status()
            match_data = response.json()
            info = match_data.get('info', {})
            participants = info.get('participants', [])
            blue_team = []
            red_team = []
            user_found = False
            for participant in participants:
                items = [participant.get(f'item{i}', 0) for i in range(7)]
                player_data = {
                    'puuid': participant.get('puuid'),
                    'summonerName': participant.get('summonerName'),
                    'championName': participant.get('championName'),
                    'championId': participant.get('championId'),
                    'teamId': participant.get('teamId'),
                    'items': items,
                    'kills': participant.get('kills', 0),
                    'deaths': participant.get('deaths', 0),
                    'assists': participant.get('assists', 0)
                }
                if participant.get('teamId') == 100:
                    blue_team.append(player_data)
                else:
                    red_team.append(player_data)
                if participant.get('puuid') == puuid:
                    win = participant.get('win', False)
                    champ = participant.get('championName', 'Neznan')
                    champ_id = participant.get('championId', 0)
                    kills = participant.get('kills', 0)
                    deaths = participant.get('deaths', 0)
                    assists = participant.get('assists', 0)
                    kda = f"{kills}/{deaths}/{assists}"
                    cs = participant.get('totalMinionsKilled', 0) + participant.get('neutralMinionsKilled', 0)
                    gold = participant.get('goldEarned', 0)
                    items = [participant.get(f'item{i}', 0) for i in range(7)]
                    spells = [participant.get(f'summoner{i}Id', 0) for i in range(1, 3)]
                    damage_dealt = participant.get('totalDamageDealtToChampions', 0)
                    damage_taken = participant.get('totalDamageTaken', 0)
                    vision_score = participant.get('visionScore', 0)
                    time_played = info.get('gameDuration', 0)
                    user_found = True
            if not user_found:
                win = 'Ni podatka'
                champ = 'Neznan'
                champ_id = 0
                kda = 'Ni podatka'
                cs = 'Ni podatka'
                gold = 'Ni podatka'
                items = []
                spells = []
                damage_dealt = 'Ni podatka'
                damage_taken = 'Ni podatka'
                vision_score = 'Ni podatka'
                time_played = 'Ni podatka'
            podrobnosti.append({
                'match_id': match_id,
                'champion': champ,
                'champion_id': champ_id,
                'win': 'Zmaga' if win == True else 'Poraz' if win == False else 'Ni podatka',
                'kda': kda,
                'cs': cs,
                'gold': gold,
                'items': items,
                'spells': spells,
                'damage_dealt': damage_dealt,
                'damage_taken': damage_taken,
                'vision_score': vision_score,
                'time_played': time_played,
                'blue_team': blue_team,
                'red_team': red_team
            })
        gui_queue.put(('Podrobnosti', podrobnosti))
        gui_queue.put(('Sporočilo', 'Podrobnosti tekem pridobljene.'))
    except requests.exceptions.HTTPError as err:
        
        gui_queue.put(('Sporočilo', f'Napaka pri pridobivanju podatkov.'))
    except Exception as err:
        
        gui_queue.put(('Sporočilo', f'Napaka pri pridobivanju podatkov.'))

def get_champion_image(champ_id):
    if champ_id in champ_images:
        return champ_images[champ_id]
    else:
        image_path = os.path.join('ChampIcons', f"{champ_id}.png")
        if os.path.exists(image_path):
            img = Image.open(image_path)
            img = img.resize((64, 64), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            champ_images[champ_id] = photo
            return photo
        else:
            return None

def get_item_image(item_id):
    if item_id in item_images:
        return item_images[item_id]
    else:
        item_info = item_data.get(item_id)
        if item_info:
            icon_path = item_info['iconPath']
            icon_filename = os.path.basename(icon_path)
            full_icon_path = os.path.join('ItemIcons', icon_filename)
            if os.path.exists(full_icon_path):
                item_img = Image.open(full_icon_path)
                item_img = item_img.resize((32, 32), Image.LANCZOS)
                item_photo = ImageTk.PhotoImage(item_img)
                item_images[item_id] = item_photo
                return item_photo
            else:
                return None
        else:
            return None

def posodobi_gui():
    try:
        while True:
            tip, vsebina = gui_queue.get_nowait()
            if tip == 'Sporočilo':
               
                if "Napaka" in vsebina:
                    status_label.config(text=vsebina, foreground='red')
                else:
                    status_label.config(text=vsebina, foreground='black')
            elif tip == 'SummonerPodatki':
                summoner_name = vsebina['summonerName']
                summoner_level = vsebina['summonerLevel']
                if summoner_name == 'Ni podatka':
                    summoner_name = 'Ni podatka'
                if summoner_level == 'Ni podatka':
                    summoner_level = 'Ni podatka'
                summoner_info_label.config(text=f" (Lvl {summoner_level})")

                def calc_win_rate(wins, losses):
                    if isinstance(wins, int) and isinstance(losses, int) and (wins + losses) > 0:
                        return int(wins * 100 / (wins + losses))
                    else:
                        return 'Ni podatka'

                def to_int(val):
                    return int(val) if str(val).isdigit() else None

                sW = to_int(vsebina['rankedSoloWins'])
                sL = to_int(vsebina['rankedSoloLosses'])
                fW = to_int(vsebina['rankedFlexWins'])
                fL = to_int(vsebina['rankedFlexLosses'])

                soloWinRate = calc_win_rate(sW, sL) if sW is not None and sL is not None else 'Ni podatka'
                flexWinRate = calc_win_rate(fW, fL) if fW is not None and fL is not None else 'Ni podatka'

                for widget in solo_frame.winfo_children():
                    widget.destroy()
                for widget in flex_frame.winfo_children():
                    widget.destroy()

                rankedSoloPath = os.path.join('RankIcons', f"{vsebina['rankedSoloTier']}.png")
                rankedFlexPath = os.path.join('RankIcons', f"{vsebina['rankedFlexTier']}.png")

                

                solo_container = tk.Frame(solo_frame)
                solo_container.pack(anchor='center')

                if os.path.exists(rankedSoloPath):
                    solo_img = Image.open(rankedSoloPath)
                    solo_img = solo_img.resize((200, 200), Image.LANCZOS)
                    solo_photo = ImageTk.PhotoImage(solo_img)
                    solo_image_label = tk.Label(solo_container, image=solo_photo)
                    solo_image_label.image = solo_photo
                    solo_image_label.pack()
                else:
                    solo_image_label = tk.Label(solo_container, text="Ni slike za SOLO.")
                    solo_image_label.pack()

                solo_text_label = tk.Label(solo_container, text=(
                    f"{vsebina['rankedSoloTier']} {vsebina['rankedSoloRank']}\n"
                    f"{vsebina['rankedSoloLP']} LP\n"
                    f"Wins: {vsebina['rankedSoloWins']}\n"
                    f"Losses: {vsebina['rankedSoloLosses']}\n"
                    f"Win Rate: {soloWinRate}%"
                ), justify='center')
                solo_text_label.pack()

                
                flex_container = tk.Frame(flex_frame)
                flex_container.pack(anchor='center')

                if os.path.exists(rankedFlexPath):
                    flex_img = Image.open(rankedFlexPath)
                    flex_img = flex_img.resize((200, 200), Image.LANCZOS)
                    flex_photo = ImageTk.PhotoImage(flex_img)
                    flex_image_label = tk.Label(flex_container, image=flex_photo)
                    flex_image_label.image = flex_photo
                    flex_image_label.pack()
                else:
                    flex_image_label = tk.Label(flex_container, text="Ni slike za FLEX.")
                    flex_image_label.pack()

                flex_text_label = tk.Label(flex_container, text=(
                    f"{vsebina['rankedFlexTier']} {vsebina['rankedFlexRank']}\n"
                    f"{vsebina['rankedFlexLP']} LP\n"
                    f"Wins: {vsebina['rankedFlexWins']}\n"
                    f"Losses: {vsebina['rankedFlexLosses']}\n"
                    f"Win Rate: {flexWinRate}%"
                ), justify='center')
                flex_text_label.pack()

            elif tip == 'Podrobnosti':
                for frame in match_frames:
                    frame.destroy()
                match_frames.clear()
                for index, item in enumerate(vsebina):
                    if item['win'] == 'Zmaga':
                        bg_color = 'lightgreen'
                    elif item['win'] == 'Poraz':
                        bg_color = 'lightcoral'
                    else:
                        bg_color = 'lightgrey'
                    frame = tk.Frame(scrollable_frame.scrollable_frame, relief='ridge', borderwidth=2, bg=bg_color)
                    frame.grid(row=index, column=0, sticky='nsew', padx=5, pady=5)
                    frame.columnconfigure(1, weight=1)
                    frame.columnconfigure(2, weight=1)
                    scrollable_frame.scrollable_frame.columnconfigure(0, weight=1)
                    match_frames.append(frame)
                    champID = item['champion_id']
                    photo = get_champion_image(champID)
                    if photo:
                        image_label = tk.Label(frame, image=photo, bg=bg_color)
                        image_label.image = photo
                        image_label.grid(row=0, column=0, rowspan=4, padx=5, pady=5, sticky='n')
                    champion = item['champion'].strip() if isinstance(item['champion'], str) else item['champion']
                    champion_label = tk.Label(frame, text=f"Champion: {champion}", bg=bg_color)
                    champion_label.grid(row=0, column=1, sticky='w')
                    win = item['win'].strip() if isinstance(item['win'], str) else item['win']
                    win_label = tk.Label(frame, text=f"Rezultat: {win}", bg=bg_color)
                    win_label.grid(row=1, column=1, sticky='w')
                    kda = item['kda'].strip() if isinstance(item['kda'], str) else item['kda']
                    kda_label = tk.Label(frame, text=f"K/D/A: {kda}", bg=bg_color)
                    kda_label.grid(row=2, column=1, sticky='w')
                    cs = item['cs']
                    cs_label = tk.Label(frame, text=f"CS: {cs}", bg=bg_color)
                    cs_label.grid(row=3, column=1, sticky='w')
                    gold = item['gold']
                    gold_label = tk.Label(frame, text=f"Gold: {gold}", bg=bg_color)
                    gold_label.grid(row=0, column=2, sticky='w')
                    items = item['items']
                    item_icons_frame = tk.Frame(frame, bg=bg_color)
                    item_icons_frame.grid(row=1, column=2, sticky='w')
                    for idx, item_id in enumerate(items):
                        if item_id == 0:
                            continue
                        item_photo = get_item_image(item_id)
                        if item_photo:
                            item_label = tk.Label(item_icons_frame, image=item_photo, bg=bg_color)
                            item_label.image = item_photo
                            item_label.grid(row=0, column=idx, padx=2)
                    expand_button = tk.Button(frame, text="+")
                    expand_button.grid(row=0, column=3, sticky='e', padx=5)
                    details_frame = tk.Frame(frame, bg=bg_color)
                    details_frame.grid(row=4, column=0, columnspan=4, sticky='nsew')
                    details_frame.grid_remove()
                    frame.expanded = False
                    def toggle_details(fr=frame, df=details_frame, eb=expand_button):
                        if fr.expanded:
                            df.grid_remove()
                            fr.expanded = False
                            eb.config(text="+")
                        else:
                            df.grid()
                            fr.expanded = True
                            eb.config(text="-")
                    expand_button.config(command=toggle_details)
                    damage_dealt = item.get('damage_dealt', 'Ni podatka')
                    damage_taken = item.get('damage_taken', 'Ni podatka')
                    vision_score = item.get('vision_score', 'Ni podatka')
                    time_played = item.get('time_played', 'Ni podatka')
                    if isinstance(time_played, int):
                        minutes = time_played // 60
                        seconds = time_played % 60
                        time_played_str = f"{minutes}m {seconds}s"
                    else:
                        time_played_str = 'Ni podatka'
                    extra_frame = tk.Frame(details_frame, bg=bg_color, relief='ridge', borderwidth=2, padx=5, pady=5)
                    extra_frame.grid(row=0, column=0, sticky='w', padx=5, pady=5)
                    damage_dealt_label = tk.Label(extra_frame, text=f"Damage Dealt: {damage_dealt}", bg=bg_color)
                    damage_dealt_label.grid(row=0, column=0, sticky='w')
                    damage_taken_label = tk.Label(extra_frame, text=f"Damage Taken: {damage_taken}", bg=bg_color)
                    damage_taken_label.grid(row=1, column=0, sticky='w')
                    vision_score_label = tk.Label(extra_frame, text=f"Vision Score: {vision_score}", bg=bg_color)
                    vision_score_label.grid(row=2, column=0, sticky='w')
                    time_played_label = tk.Label(extra_frame, text=f"Time Played: {time_played_str}", bg=bg_color)
                    time_played_label.grid(row=3, column=0, sticky='w')
                    teams_frame = tk.Frame(details_frame, bg=bg_color)
                    teams_frame.grid(row=1, column=0, columnspan=4, sticky='nsew', pady=10)
                    blue_team_frame = tk.Frame(teams_frame, bg=bg_color, relief='ridge', borderwidth=2, padx=5, pady=5)
                    blue_team_frame.grid(row=0, column=0, sticky='nw', padx=5, pady=5)
                    blue_team_label = tk.Label(blue_team_frame, text="Modra ekipa:", bg=bg_color, font=('Arial', 12, 'bold'))
                    blue_team_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
                    for idx_p, player in enumerate(item['blue_team']):
                        player_frame = tk.Frame(blue_team_frame, bg=bg_color, relief='groove', borderwidth=1, padx=5, pady=5)
                        player_frame.grid(row=idx_p+1, column=0, sticky='w', pady=2)
                        champ_id = player['championId']
                        summoner_name = player['summonerName']
                        champ_photo = get_champion_image(champ_id)
                        if champ_photo:
                            champ_label = tk.Label(player_frame, image=champ_photo, bg=bg_color)
                            champ_label.image = champ_photo
                            champ_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
                        else:
                            champ_label = tk.Label(player_frame, text="Ni slike", bg=bg_color)
                            champ_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
                        name_label = tk.Label(player_frame, text=summoner_name, bg=bg_color)
                        name_label.grid(row=0, column=1, sticky='w', padx=5)
                        kda_label = tk.Label(player_frame, text=f"{player['kills']}/{player['deaths']}/{player['assists']}", bg=bg_color)
                        kda_label.grid(row=0, column=2, sticky='w', padx=5)
                        player_item_icons_frame = tk.Frame(player_frame, bg=bg_color)
                        player_item_icons_frame.grid(row=0, column=3, sticky='w', padx=5)
                        for i_idx, p_item_id in enumerate(player['items']):
                            if p_item_id == 0:
                                continue
                            p_item_photo = get_item_image(p_item_id)
                            if p_item_photo:
                                p_item_label = tk.Label(player_item_icons_frame, image=p_item_photo, bg=bg_color)
                                p_item_label.image = p_item_photo
                                p_item_label.grid(row=0, column=i_idx, padx=2)
                    red_team_frame = tk.Frame(teams_frame, bg=bg_color, relief='ridge', borderwidth=2, padx=5, pady=5)
                    red_team_frame.grid(row=0, column=1, sticky='nw', padx=20, pady=5)
                    red_team_label = tk.Label(red_team_frame, text="Rdeča ekipa:", bg=bg_color, font=('Arial', 12, 'bold'))
                    red_team_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
                    for idx_p, player in enumerate(item['red_team']):
                        player_frame = tk.Frame(red_team_frame, bg=bg_color, relief='groove', borderwidth=1, padx=5, pady=5)
                        player_frame.grid(row=idx_p+1, column=0, sticky='w', pady=2)
                        champ_id = player['championId']
                        summoner_name = player['summonerName']
                        champ_photo = get_champion_image(champ_id)
                        if champ_photo:
                            champ_label = tk.Label(player_frame, image=champ_photo, bg=bg_color)
                            champ_label.image = champ_photo
                            champ_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
                        else:
                            champ_label = tk.Label(player_frame, text="Ni slike", bg=bg_color)
                            champ_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
                        name_label = tk.Label(player_frame, text=summoner_name, bg=bg_color)
                        name_label.grid(row=0, column=1, sticky='w', padx=5)
                        kda_label = tk.Label(player_frame, text=f"{player['kills']}/{player['deaths']}/{player['assists']}", bg=bg_color)
                        kda_label.grid(row=0, column=2, sticky='w', padx=5)
                        player_item_icons_frame = tk.Frame(player_frame, bg=bg_color)
                        player_item_icons_frame.grid(row=0, column=3, sticky='w', padx=5)
                        for i_idx, p_item_id in enumerate(player['items']):
                            if p_item_id == 0:
                                continue
                            p_item_photo = get_item_image(p_item_id)
                            if p_item_photo:
                                p_item_label = tk.Label(player_item_icons_frame, image=p_item_photo, bg=bg_color)
                                p_item_label.image = p_item_photo
                                p_item_label.grid(row=0, column=i_idx, padx=2)
                for i in range(len(vsebina)):
                    scrollable_frame.scrollable_frame.rowconfigure(i, weight=1)
                scrollable_frame.scrollable_frame.update_idletasks()
    except queue.Empty:
        pass
    root.after(100, posodobi_gui)

root = tk.Tk()
root.title("Riot Games API")
root.geometry('1000x900')
root.columnconfigure(0, weight=1)
style = ttk.Style(root)
style.theme_use('clam')

vnos_frame = ttk.Frame(root)
vnos_frame.pack(pady=10, fill='x')
ttk.Label(vnos_frame, text="Vnesi Riot ID:").grid(row=0, column=0, padx=5, pady=5)
vnos_ime = ttk.Entry(vnos_frame)
vnos_ime.grid(row=0, column=1, padx=5, pady=5)
ttk.Label(vnos_frame, text="Vnesi gameTag:").grid(row=1, column=0, padx=5, pady=5)
vnos_GameTag = ttk.Entry(vnos_frame)
vnos_GameTag.grid(row=1, column=1, padx=5, pady=5)
gumb_vse = ttk.Button(vnos_frame, text="Pridobi podatke", command=pridobi_vse)
gumb_vse.grid(row=0, column=2, rowspan=2, padx=10, pady=5)

summoner_info_label = ttk.Label(root, text="")
summoner_info_label.pack(pady=5)

rank_frame = tk.Frame(root)
rank_frame.pack(pady=5)
rank_frame.columnconfigure(0, weight=1)
rank_frame.columnconfigure(1, weight=1)

solo_frame = tk.Frame(rank_frame)
solo_frame.grid(row=0, column=0, padx=5, sticky='nsew')

flex_frame = tk.Frame(rank_frame)
flex_frame.grid(row=0, column=1, padx=5, sticky='nsew')

status_label = ttk.Label(root, text="")
status_label.pack(pady=5)

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

scrollable_frame = ScrollableFrame(root)
scrollable_frame.pack(pady=10, fill='both', expand=True)
nalozi_item_data()
root.after(100, posodobi_gui)
root.mainloop()
