from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
import time
import requests
import re
import hashlib
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import ssl
import certifi

class WebScraper:
    def __init__(self, output_folder):
        self.output_folder = output_folder
        self.css_folder = os.path.join(output_folder, "css")
        self.js_folder = os.path.join(output_folder, "js")
        self.images_folder = os.path.join(output_folder, "images")
        self.create_folders()
        self.session = self.create_session()
        
        # Configuration de Chrome avec options SSL
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        from chromedriver_py import binary_path
        service = Service(binary_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def create_session(self):
        """Crée une session requests configurée avec retry et SSL"""
        session = requests.Session()
        
        # Configuration des retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Configuration de l'adaptateur avec SSL vérifié
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Configuration du contexte SSL
        session.verify = certifi.where()
        
        return session

    def create_folders(self):
        """Crée les dossiers nécessaires pour organiser les fichiers"""
        folders = [self.output_folder, self.css_folder, self.js_folder, self.images_folder]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)

    def generate_filename(self, content, extension):
        """Génère un nom de fichier unique basé sur le contenu"""
        if isinstance(content, str):
            content = content.encode()
        hash_object = hashlib.md5(content)
        return f"{hash_object.hexdigest()[:8]}{extension}"

    def download_external_file(self, url, folder):
        """Télécharge un fichier externe avec gestion des erreurs améliorée"""
        try:
            # Ajout d'un User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            
            # Gestion améliorée des types de fichiers
            if not file_name or '.' not in file_name:
                content_type = response.headers.get('content-type', '').lower()
                if 'javascript' in content_type:
                    file_name = self.generate_filename(response.text, '.js')
                elif 'css' in content_type:
                    file_name = self.generate_filename(response.text, '.css')
                elif 'image' in content_type:
                    extension = '.' + content_type.split('/')[-1].split(';')[0]
                    file_name = self.generate_filename(response.content, extension)
                else:
                    print(f"Type de contenu non supporté pour {url}: {content_type}")
                    return None
            
            local_path = os.path.join(folder, file_name)
            
            # Vérification si le fichier existe déjà
            if not os.path.exists(local_path):
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Fichier téléchargé: {local_path}")
            else:
                print(f"Fichier déjà existant: {local_path}")
            
            return os.path.relpath(local_path, self.output_folder)
            
        except requests.exceptions.SSLError as e:
            print(f"Erreur SSL lors du téléchargement de {url}: {e}")
            # Tentative sans vérification SSL en dernier recours
            try:
                response = self.session.get(url, headers=headers, verify=False, timeout=10)
                # ... (même logique que précédemment)
            except Exception as e:
                print(f"Échec du téléchargement même sans SSL pour {url}: {e}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du téléchargement de {url}: {e}")
            return None
        except Exception as e:
            print(f"Erreur inattendue lors du téléchargement de {url}: {e}")
            return None

    def extract_inline_styles(self, soup):
        """Extrait les styles CSS inline"""
        style_tags = soup.find_all('style')
        for idx, style in enumerate(style_tags):
            if style.string:
                filename = self.generate_filename(style.string, '.css')
                css_path = os.path.join(self.css_folder, filename)
                
                if not os.path.exists(css_path):
                    with open(css_path, 'w', encoding='utf-8') as f:
                        f.write(style.string)
                    print(f"Style CSS extrait: {css_path}")
                
                new_link = soup.new_tag('link', rel='stylesheet', href=f'css/{filename}')
                style.replace_with(new_link)

    def extract_inline_scripts(self, soup):
        """Extrait les scripts JS inline"""
        script_tags = soup.find_all('script', string=True)
        for idx, script in enumerate(script_tags):
            if script.string and not script.get('src'):
                filename = self.generate_filename(script.string, '.js')
                js_path = os.path.join(self.js_folder, filename)
                
                if not os.path.exists(js_path):
                    with open(js_path, 'w', encoding='utf-8') as f:
                        f.write(script.string)
                    print(f"Script JS extrait: {js_path}")
                
                new_script = soup.new_tag('script', src=f'js/{filename}')
                script.replace_with(new_script)

    def process_external_resources(self, soup, base_url):
        """Traite les ressources externes"""
        # CSS externe
        for link in soup.find_all('link', href=True):
            if link['href'].endswith('.css'):
                css_url = urljoin(base_url, link['href'])
                local_path = self.download_external_file(css_url, self.css_folder)
                if local_path:
                    link['href'] = local_path

        # JavaScript externe
        for script in soup.find_all('script', src=True):
            js_url = urljoin(base_url, script['src'])
            local_path = self.download_external_file(js_url, self.js_folder)
            if local_path:
                script['src'] = local_path

        # Images
        for img in soup.find_all('img', src=True):
            img_url = urljoin(base_url, img['src'])
            local_path = self.download_external_file(img_url, self.images_folder)
            if local_path:
                img['src'] = local_path

    def scrape(self, url):
        """Fonction principale de scraping"""
        try:
            print(f"Démarrage du scraping de {url}...")
            
            # Désactiver les avertissements SSL pour requests
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            self.driver.get(url)
            time.sleep(5)  # Augmentation du temps d'attente
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            print("Extraction des styles inline...")
            self.extract_inline_styles(soup)
            
            print("Extraction des scripts inline...")
            self.extract_inline_scripts(soup)
            
            print("Traitement des ressources externes...")
            self.process_external_resources(soup, url)
            
            html_path = os.path.join(self.output_folder, "index.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            print("Scraping terminé avec succès!")
            return True
            
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            return False
            
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = WebScraper("website_files_2")
    scraper.scrape("https://phenix-bat-tech.com/")