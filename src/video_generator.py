import fitz  # PyMuPDF
import cv2
import numpy as np
import moviepy.video.io.ImageSequenceClip as ImageSequenceClip
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re

def clean_filename(filename):
    base, ext = os.path.splitext(filename)  # Sépare le nom et l'extension
    base = re.sub(r'[^a-zA-Z0-9]', '_', base)  # Nettoie le nom sans toucher à l'extension
    base = re.sub(r'_+', '_', base).strip('_')
    return f"{base}{ext}"  # Recolle l'extension


def save_images_to_folder(images, dates, video_name):
    """Sauvegarde les images dans un dossier spécifique avec le format photo_DateLier_id"""
    # Créer le dossier output/NomDeLaVideo
    output_dir = os.path.join("output", video_name.replace('.mp4', ''))
    os.makedirs(output_dir, exist_ok=True)
    
    saved_images = []
    for i, (img, date) in enumerate(zip(images, dates)):
        # Nettoyer la date pour le nom de fichier
        clean_date = clean_filename(date)
        # Générer le nom du fichier avec le format photo_DateLier_id
        image_filename = f"photo_{clean_date}_{i:03d}.jpg"
        image_path = os.path.join(output_dir, image_filename)
        
        # Sauvegarder l'image
        img.save(image_path, "JPEG", quality=95)
        saved_images.append(image_path)
    
    return output_dir, saved_images

def extract_images_and_dates_from_pdf(pdf_path):
    """Extrait les images et dates en maintenant la correspondance correcte"""
    doc = fitz.open(pdf_path)
    all_images = []
    all_dates = []
    
    # Extraire toutes les dates du document
    all_date_entries = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        for line in text.split("\n"):
            line = line.strip()
            if any(month in line for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                if any(indicator in line for indicator in ["th", "st", "nd", "rd"]) and "25" in line:
                    all_date_entries.append(line)
    
    # Éliminer les doublons tout en préservant l'ordre
    unique_dates = []
    for date in all_date_entries:
        if date not in unique_dates:
            unique_dates.append(date)
    
    # Extraire les images et filtrer
    image_hashes = set()  # Pour filtrer les doublons
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        
        for img_info in image_list:
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            try:
                img = Image.open(io.BytesIO(image_bytes))
                
                # Filtrer les images trop petites ou non pertinentes
                if img.width >= 300 and img.height >= 300:
                    # Vérifier si c'est un doublon
                    img_hash = hash(img.tobytes())
                    if img_hash not in image_hashes:
                        image_hashes.add(img_hash)
                        all_images.append(img)
            except Exception as e:
                print(f"Erreur lors du traitement d'une image: {e}")
                continue
    
    print(f"Nombre total d'images valides: {len(all_images)}")
    print(f"Nombre total de dates uniques: {len(unique_dates)}")
    
    # Inverser les deux listes pour commencer par la fin
    all_images.reverse()
    unique_dates.reverse()
    
    # Associer les dates aux images
    result_images = []
    result_dates = []
    
    if len(all_images) > 0 and len(unique_dates) > 0:
        # Calculer combien d'images par date en moyenne
        images_per_date = len(all_images) / len(unique_dates)
        print(f"Estimation: environ {images_per_date:.1f} images par date")
        
        for i, img in enumerate(all_images):
            date_index = min(int(i / images_per_date), len(unique_dates) - 1)
            result_images.append(img)
            result_dates.append(unique_dates[date_index])
    
    return result_images, result_dates

def extract_dates_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    dates = []
    for page in doc:
        text = page.get_text("text")
        for line in text.split("\n"):
            if any(month in line for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                dates.append(line.strip())
    return dates

def add_date_to_images(images, dates):
    edited_images = []
    try:
        font = ImageFont.truetype("Arial", 20)  # Essayez d'utiliser Arial
    except:
        font = ImageFont.load_default()  # Fallback si Arial n'est pas disponible
    
    # Les dates sont déjà inversées dans extract_images_and_dates_from_pdf
    # Ne pas les inverser une seconde fois ici
    
    # Préparer les dates pour les distribuer sur les images
    if len(dates) > 0 and len(images) > 0:
        # Calculer combien d'images en moyenne par date
        avg_images_per_date = len(images) / len(dates)
        print(f"En moyenne, il y a {avg_images_per_date:.2f} images par date")
        
        # Assigner les dates aux images
        image_dates = []
        for i in range(len(images)):
            # Trouver la date correspondante
            date_index = min(int(i / avg_images_per_date), len(dates) - 1)
            image_dates.append(dates[date_index])
    else:
        image_dates = [""] * len(images)
    
    print(f"Distribution des dates : {len(dates)} dates pour {len(images)} images")
    
    for i, img in enumerate(images):
        # Convertir en mode RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        img_copy = img.copy()  # Créer une copie pour ne pas modifier l'original
        draw = ImageDraw.Draw(img_copy)
        
        # Positionner la date en bas à gauche
        text_position = (10, img_copy.height - 30)
        date = image_dates[i] if i < len(image_dates) else ""
        
        # Ajouter un fond noir sous le texte pour meilleure lisibilité
        # Utiliser la nouvelle méthode dans PIL récent
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(date)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        elif hasattr(draw, 'textsize'):
            text_width, text_height = draw.textsize(date, font=font)
        else:
            # Estimation approximative si aucune méthode n'est disponible
            text_width, text_height = len(date) * 10, 20
        
        draw.rectangle(
            [text_position[0], text_position[1], text_position[0] + text_width, text_position[1] + text_height],
            fill=(0, 0, 0, 128)
        )
        
        # Ajouter le texte
        draw.text(text_position, date, fill=(255, 255, 255), font=font)
        edited_images.append(img_copy)
    
    return edited_images

def images_to_video(images, dates, output_path, duration=2, fps=1):
    """Crée une vidéo à partir des images avec leur date"""
    if not images:
        print("Aucune image à inclure dans la vidéo.")
        return
        
    # Limiter la durée totale de la vidéo à 3 minutes maximum
    total_images = len(images)
    if total_images * duration > 180:  # 3 minutes = 180 secondes
        duration = max(1, int(180 / total_images))
        print(f"Durée ajustée à {duration} secondes par image pour limiter la vidéo à 3 minutes")
    
    # Normaliser la taille des images si nécessaire
    max_width = max(img.width for img in images)
    max_height = max(img.height for img in images)
    
    normalized_images = []
    for img in images:
        if img.width != max_width or img.height != max_height:
            # Créer une nouvelle image avec la taille maximale
            new_img = Image.new('RGB', (max_width, max_height), (0, 0, 0))
            # Centrer l'image originale
            x_offset = (max_width - img.width) // 2
            y_offset = (max_height - img.height) // 2
            new_img.paste(img, (x_offset, y_offset))
            normalized_images.append(new_img)
        else:
            normalized_images.append(img)
    
    # Convertir les images PIL en tableaux numpy
    np_images = [np.array(img) for img in normalized_images]
    
    # Répéter chaque image pour atteindre la durée souhaitée
    # Par exemple, si fps=1 et duration=2, chaque image apparaît 2 fois
    expanded_frames = []
    for img in np_images:
        frames_for_this_img = [img] * int(fps * duration)
        expanded_frames.extend(frames_for_this_img)
    
    # Créer la vidéo avec les frames répétées
    clip = ImageSequenceClip.ImageSequenceClip(expanded_frames, fps=fps)
    
    # Écrire la vidéo
    print(f"Nom du fichier vidéo généré : {output_path}")
    clip.write_videofile(output_path, fps=fps, codec="libx264")

def generate_video(pdf_file, output_path, verbose=False):
    """Génère une vidéo à partir du PDF."""
    # Créer le dossier output s'il n'existe pas
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # Chemin complet pour la vidéo
    video_path = os.path.join(output_dir, clean_filename(output_path))
    
    if verbose:
        print("Extraction des images et dates du PDF...")
    
    images, dates = extract_images_and_dates_from_pdf(pdf_file)

    if len(images) == 0:
        print("Aucune image n'a été trouvée dans le PDF. Vérifiez que le PDF contient bien des images.")
        return

    if verbose:
        print("Ajout des dates aux images...")
    edited_images = add_date_to_images(images, dates)
    
    if verbose:
        print("Sauvegarde des images...")
    images_dir, _ = save_images_to_folder(edited_images, dates, os.path.basename(output_path))
    
    if verbose:
        print(f"Images sauvegardées dans : {images_dir}")
        print("Création de la vidéo...")

    images_to_video(edited_images, dates, video_path, duration=2)
    
    if verbose:
        print(f"Vidéo créée avec succès: {video_path}")
        
    return video_path