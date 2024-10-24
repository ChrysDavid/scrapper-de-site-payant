from selenium import webdriver 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        self.visited_urls = set()  # Pour suivre les pages déjà visitées
        self.base_domain = ""  # Pour limiter le scraping à un domaine
        self.create_folders()
        self.session = self.create_session()
        
        # Configuration de Chrome avec options SSL
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        
        from chromedriver_py import binary_path
        service = Service(binary_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def create_session(self):
        """Crée une session requests configurée avec retry et SSL"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
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
            if not os.path.exists(local_path):
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Fichier téléchargé: {local_path}")
            else:
                print(f"Fichier déjà existant: {local_path}")
            
            return os.path.relpath(local_path, self.output_folder)
            
        except requests.exceptions.SSLError as e:
            print(f"Erreur SSL lors du téléchargement de {url}: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du téléchargement de {url}: {e}")
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
        for link in soup.find_all('link', href=True):
            if link['href'].endswith('.css'):
                css_url = urljoin(base_url, link['href'])
                local_path = self.download_external_file(css_url, self.css_folder)
                if local_path:
                    link['href'] = local_path

        for script in soup.find_all('script', src=True):
            js_url = urljoin(base_url, script['src'])
            local_path = self.download_external_file(js_url, self.js_folder)
            if local_path:
                script['src'] = local_path

        for img in soup.find_all('img', src=True):
            img_url = urljoin(base_url, img['src'])
            local_path = self.download_external_file(img_url, self.images_folder)
            if local_path:
                img['src'] = local_path

    def scrape_page(self, url):
        """Scrape une page et enregistre son contenu"""
        try:
            if url in self.visited_urls:
                print(f"Page déjà visitée : {url}")
                return

            print(f"Démarrage du scraping de {url}...")
            self.visited_urls.add(url)

            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            print("Extraction des styles inline...")
            self.extract_inline_styles(soup)
            
            print("Extraction des scripts inline...")
            self.extract_inline_scripts(soup)
            
            print("Traitement des ressources externes...")
            self.process_external_resources(soup, url)
            
            parsed_url = urlparse(url)
            page_name = "index.html" if parsed_url.path == "/" else parsed_url.path.strip("/").replace("/", "_") + ".html"
            html_path = os.path.join(self.output_folder, page_name)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            print(f"Page {url} sauvegardée avec succès!")
            
            # Suivre les liens internes
            for link in soup.find_all('a', href=True):
                next_url = urljoin(url, link['href'])
                if self.is_internal_link(next_url):
                    self.scrape_page(next_url)
            
        except Exception as e:
            print(f"Erreur lors du scraping de {url}: {e}")

    def is_internal_link(self, url):
        """Vérifie si le lien est interne au domaine principal"""
        parsed_url = urlparse(url)
        return parsed_url.netloc == self.base_domain

    def start_scraping(self, start_url):
        """Lance le scraping à partir de l'URL de départ"""
        self.base_domain = urlparse(start_url).netloc
        self.scrape_page(start_url)

    def close(self):
        """Ferme le navigateur et nettoie les ressources"""
        self.driver.quit()

# Utilisation du scraper
output_folder = "site_content"
scraper = WebScraper(output_folder)

start_url = "https://phenix-bat-tech.com/"  # URL de départ du site web à scraper
scraper.start_scraping(start_url)
scraper.close()
