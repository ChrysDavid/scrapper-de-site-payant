import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Dossier de base pour les fichiers téléchargés
output_folder = "downloaded_site_13"

# Crée les dossiers s'ils n'existent pas
os.makedirs(output_folder, exist_ok=True)

# Fonction pour télécharger et enregistrer un fichier
def download_file(url, base_folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Extraire le chemin du fichier à partir de l'URL
            parsed_url = urlparse(url)
            file_path = parsed_url.path.lstrip("/")  # Supprimer le "/" initial du chemin

            # Supprimer le préfixe "demo_html_indisoft_" du chemin si présent
            file_path = file_path.replace("demo/html/indisoft/", "")

            # Déterminer le chemin complet du fichier local
            local_file_path = os.path.join(base_folder, file_path)
            local_folder = os.path.dirname(local_file_path)

            # Créer les dossiers locaux s'ils n'existent pas
            os.makedirs(local_folder, exist_ok=True)

            # Télécharger et sauvegarder le fichier
            with open(local_file_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {url}")
        else:
            print(f"Failed to download {url}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Fonction pour extraire et télécharger les fichiers HTML, CSS, JS, Images, Fonts, etc.
def scrape_files(url, base_folder, visited_pages=set()):
    try:
        # Télécharger la page HTML principale
        response = requests.get(url)
        if response.status_code == 200:
            visited_pages.add(url)

            # Sauvegarder la page HTML principale
            soup = BeautifulSoup(response.text, 'html.parser')
            page_filename = get_filename_from_url(url)
            download_file(url, base_folder)

            # Scraper les liens CSS
            for link in soup.find_all('link', href=True):
                file_url = urljoin(url, link['href'])
                if link['href'].endswith('.css'):
                    download_file(file_url, base_folder)

            # Scraper les scripts JS
            for script in soup.find_all('script', src=True):
                file_url = urljoin(url, script['src'])
                if file_url.endswith('.js'):
                    download_file(file_url, base_folder)

            # Scraper les images et autres fichiers (ex: favicons, médias)
            for img in soup.find_all(['img', 'source'], src=True):
                file_url = urljoin(url, img['src'])
                download_file(file_url, base_folder)

            # Scraper tous les liens vers d'autres pages HTML du même site
            for a_tag in soup.find_all('a', href=True):
                next_page = urljoin(url, a_tag['href'])

                # Filtrer uniquement les liens HTML internes (et non des ressources externes ou autres types de fichiers)
                if is_internal_html(next_page, url) and next_page not in visited_pages:
                    print(f"Scraping linked page: {next_page}")
                    scrape_files(next_page, base_folder, visited_pages)

            print("Scraping terminé.")
        else:
            print(f"Erreur: Impossible de récupérer la page. Status code {response.status_code}")
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")

# Vérifie si un lien est une page HTML interne
def is_internal_html(link, base_url):
    parsed_link = urlparse(link)
    parsed_base = urlparse(base_url)

    # Comparer les noms de domaine et vérifier si c'est une page HTML
    return parsed_link.netloc == parsed_base.netloc and (parsed_link.path.endswith('.html') or parsed_link.path == '')

# Génère un nom de fichier unique pour une page en fonction de son URL
def get_filename_from_url(url):
    parsed_url = urlparse(url)
    if parsed_url.path == "" or parsed_url.path == "/":
        return "index.html"
    else:
        path = parsed_url.path.strip("/").replace("/", "_")
        if not path.endswith(".html"):
            path += ".html"
        return path

# Exemple d'utilisation
if __name__ == "__main__":
    url_to_scrape = "https://zrtechsolutions.com/demo/html/indisoft/index.html"  # Remplacez par l'URL à scraper
    scrape_files(url_to_scrape, output_folder)
