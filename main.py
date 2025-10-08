import requests
import time
import string
import random
from itertools import product

class DiscordUsernameChecker:
    def __init__(self, proxy_list=None):
        self.base_url = "https://discord.com/api/v10/unique-username/username-attempt-unauthed"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.delay = 2.0  # Sekunden zwischen Anfragen
        self.available_names = []
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
        self.proxy_errors = {}  # Zählt Fehler pro Proxy
        
    def get_next_proxy(self):
        """Gibt den nächsten Proxy aus der Liste zurück"""
        if not self.proxy_list:
            return None
        
        # Rotiere durch Proxies
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        
        # Format: {"http": "http://ip:port", "https": "http://ip:port"}
        return {
            "http": proxy,
            "https": proxy
        }
    
    def mark_proxy_error(self, proxy):
        """Markiert einen Proxy als fehlerhaft"""
        if proxy:
            proxy_url = proxy.get("http", "unknown")
            self.proxy_errors[proxy_url] = self.proxy_errors.get(proxy_url, 0) + 1
            
            # Entferne Proxy nach 3 Fehlern
            if self.proxy_errors[proxy_url] >= 3:
                print(f"⚠️  Proxy {proxy_url} wird entfernt (zu viele Fehler)")
                if proxy_url in self.proxy_list:
                    self.proxy_list.remove(proxy_url)
    
    def check_username(self, username):
        """Prüft ob ein Username verfügbar ist"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                proxy = self.get_next_proxy()
                payload = {"username": username}
                
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers,
                    proxies=proxy,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Wenn 'taken' False ist, ist der Name verfügbar
                    return not data.get('taken', True)
                elif response.status_code == 429:
                    # Rate limit erreicht
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"⚠️  Rate-Limit erreicht. Warte {retry_after} Sekunden...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"❌ Fehler {response.status_code} bei {username}")
                    return None
                    
            except requests.exceptions.ProxyError:
                print(f"❌ Proxy-Fehler bei {username}, versuche nächsten Proxy...")
                self.mark_proxy_error(proxy)
                if attempt < max_retries - 1:
                    continue
                return None
            except requests.exceptions.Timeout:
                print(f"⏱️  Timeout bei {username}, versuche erneut...")
                if attempt < max_retries - 1:
                    continue
                return None
            except Exception as e:
                print(f"❌ Fehler bei {username}: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                return None
        
        return None
    
    def generate_random_names(self, count=50, include_numbers=True):
        """Generiert zufällige 3-Zeichen-Namen"""
        names = set()
        if include_numbers:
            chars = string.ascii_lowercase + string.digits  # a-z und 0-9
        else:
            chars = string.ascii_lowercase
        
        while len(names) < count:
            name = ''.join(random.choices(chars, k=3))
            names.add(name)
        
        return list(names)
    
    def generate_all_combinations(self, include_numbers=True):
        """Generiert alle möglichen 3-Zeichen-Kombinationen"""
        if include_numbers:
            chars = string.ascii_lowercase + string.digits  # 36 Zeichen = 46.656 Kombinationen
        else:
            chars = string.ascii_lowercase  # 26 Zeichen = 17.576 Kombinationen
        
        print(f"ℹ️  Generiere {len(chars)**3} Kombinationen...")
        return [''.join(combo) for combo in product(chars, repeat=3)]
    
    def check_names(self, names, max_check=None):
        """Prüft eine Liste von Namen"""
        if max_check:
            names = names[:max_check]
        
        print(f"🔍 Prüfe {len(names)} Namen...\n")
        
        for i, name in enumerate(names, 1):
            print(f"[{i}/{len(names)}] Prüfe: {name}...", end=" ")
            
            is_available = self.check_username(name)
            
            if is_available:
                print("✅ VERFÜGBAR!")
                self.available_names.append(name)
            elif is_available is False:
                print("❌ Vergeben")
            else:
                print("⚠️  Fehler")
            
            # Rate-Limiting: Warte zwischen Anfragen
            if i < len(names):
                time.sleep(self.delay)
        
        return self.available_names
    
    def save_results(self, filename="verfuegbare_namen.txt"):
        """Speichert verfügbare Namen in Datei"""
        if self.available_names:
            with open(filename, 'w') as f:
                for name in self.available_names:
                    f.write(f"{name}\n")
            print(f"\n💾 {len(self.available_names)} verfügbare Namen in '{filename}' gespeichert")
        else:
            print("\n❌ Keine verfügbaren Namen gefunden")


def load_proxies_from_file(filename="proxies.txt"):
    """Lädt Proxies aus einer Datei"""
    try:
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        print(f"✅ {len(proxies)} Proxies aus '{filename}' geladen")
        return proxies
    except FileNotFoundError:
        print(f"⚠️  Datei '{filename}' nicht gefunden")
        return []


def main():
    # ===== PROXY KONFIGURATION =====
    # Füge hier deine Proxies ein (Format: http://ip:port oder http://user:pass@ip:port)
    PROXIES = [
        # Beispiele (ersetze mit deinen echten Proxies):
        # "http://123.45.67.89:8080",
        # "http://98.76.54.32:3128",
        # "http://username:password@12.34.56.78:8080",
    ]
    
    # Oder lade Proxies aus einer Datei
    # PROXIES = load_proxies_from_file("proxies.txt")
    # ================================
    
    checker = DiscordUsernameChecker(proxy_list=PROXIES)
    
    if PROXIES:
        print(f"🔒 Verwende {len(PROXIES)} Proxy(s)")
    else:
        print("⚠️  Keine Proxies konfiguriert - verwende direkte Verbindung")
    
    print("=" * 50)
    print("Discord 3-Zeichen Username Checker")
    print("=" * 50)
    print("\nOptionen:")
    print("1 - Zufällige Namen prüfen (empfohlen)")
    print("2 - Alle Kombinationen prüfen (dauert SEHR lange!)")
    print("3 - Eigene Namen eingeben")
    
    choice = input("\nWähle Option (1-3): ").strip()
    
    # Zahlen einbeziehen?
    include_nums = input("Zahlen (0-9) einbeziehen? (ja/nein, Standard: ja): ").lower()
    include_numbers = include_nums != "nein"
    
    if choice == "1":
        count = input("Wie viele zufällige Namen? (Standard: 50): ").strip()
        count = int(count) if count.isdigit() else 50
        names = checker.generate_random_names(count, include_numbers)
        
    elif choice == "2":
        if include_numbers:
            print("\n⚠️  WARNUNG: Es gibt 46.656 mögliche 3-Zeichen-Kombinationen (a-z + 0-9)!")
            print("Mit 2 Sekunden Delay dauert das ~26 Stunden!")
        else:
            print("\n⚠️  WARNUNG: Es gibt 17.576 mögliche 3-Zeichen-Kombinationen (nur a-z)!")
            print("Mit 2 Sekunden Delay dauert das ~10 Stunden!")
        confirm = input("Trotzdem fortfahren? (ja/nein): ").lower()
        if confirm != "ja":
            return
        names = checker.generate_all_combinations(include_numbers)
        
    elif choice == "3":
        names_input = input("Namen eingeben (kommagetrennt, z.B. abc,xy7,l0l): ")
        names = [n.strip().lower() for n in names_input.split(",")]
        # Filtere nur 3-Zeichen-Namen
        names = [n for n in names if len(n) == 3]
        
    else:
        print("Ungültige Auswahl!")
        return
    
    # Namen prüfen
    available = checker.check_names(names)
    
    # Ergebnisse anzeigen
    print("\n" + "=" * 50)
    print(f"✅ Gefunden: {len(available)} verfügbare Namen")
    print("=" * 50)
    
    if available:
        print("\nVerfügbare Namen:")
        for name in available:
            print(f"  • {name}")
        
        # Speichern
        save = input("\nErgebnisse speichern? (ja/nein): ").lower()
        if save == "ja":
            checker.save_results()


if __name__ == "__main__":
    main()
