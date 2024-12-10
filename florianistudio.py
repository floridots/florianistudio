import flet as ft
from PIL import Image, ImageEnhance
import piexif
from datetime import datetime
import os
import base64
import webbrowser

def apply_watermark(file_path, watermark_path):
    img = Image.open(file_path).convert("RGBA")
    watermark = Image.open(watermark_path).convert("RGBA")
    img_width, img_height = img.size
    diagonal = (img_width**2 + img_height**2) ** 0.5
    watermark_size = int(diagonal * 0.18)
    watermark = watermark.resize((watermark_size, watermark_size), Image.LANCZOS)
    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(0.4)
    watermark.putalpha(alpha)
    watermark = watermark.rotate(45, expand=True)
    watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for y in range(-watermark_size, img_height, int(watermark_size * 0.9)):
        for x in range(-watermark_size, img_width, int(watermark_size * 0.9)):
            watermark_layer.paste(watermark, (x, y), watermark)
    watermarked_image = Image.alpha_composite(img, watermark_layer)
    watermarked_image = watermarked_image.convert("RGB")
    base_name, ext = os.path.splitext(file_path)
    output_path = f"{base_name}_watermarked{ext}"
    watermarked_image.save(output_path, "jpeg")
    return output_path

def process_image(file_path):
    img = Image.open(file_path)
    img = img.convert("RGB")
    exif_data_before = img.info.get("exif")
    exif_dict_before = piexif.load(exif_data_before) if exif_data_before else {}
    exif_dict = piexif.load(exif_data_before) if exif_data_before else {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}, "Interop": {}, "thumbnail": None}
    for key in exif_dict.keys():
        exif_dict[key] = {}
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Artist: "Felipe Floriani Lopes da Nobrega",
            piexif.ImageIFD.ImageDescription: f"Criado em {current_datetime} - FlorianiStudio".encode('utf-8'),
            piexif.ImageIFD.XPComment: "Contato: felipeffloriani@gmail.com | +5511915559839 | instagram.com/florianistudio".encode('utf-16')
        },
        "Exif": {
            piexif.ExifIFD.UserComment: "Projeto de design gráfico".encode('utf-16')
        },
        "1st": {},
        "GPS": {},
        "Interop": {},
        "thumbnail": None,
    }
    exif_dict_after = exif_dict
    exif_bytes = piexif.dump(exif_dict)
    base_name, ext = os.path.splitext(file_path)
    output_path = f"{base_name}_Mfix{ext}"
    img.save(output_path, "jpeg", exif=exif_bytes)
    return output_path, exif_dict_before, exif_dict_after

def convert_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def close_metadata_dialog(e, dialog):
    dialog.open = False
    e.page.update()

def main(page: ft.Page):
    page.title = "Floriani Studio - Aplicador de Marca D'\u00e1gua e Editor de Metadados"
    page.window.width = 800
    page.window.height = 600
    page.padding = 20
    page.spacing = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.window_icon = "assets/icone.png"
    file_metadata = []
    preview_images = []

    def on_files_upload(e):
        if e.files:
            output_paths = []
            preview_images.clear()
            file_metadata.clear()
            preview_gallery.controls.clear()
            for file in e.files:
                file_path = file.path
                output_path_watermark = apply_watermark(file_path, "logo render.png")
                if "Erro" in output_path_watermark:
                    status_text.value = output_path_watermark
                    page.update()
                    return
                output_path_metadata, exif_before, exif_after = process_image(output_path_watermark)
                if "Erro" in output_path_metadata:
                    status_text.value = output_path_metadata
                    page.update()
                    return
                output_paths.append(output_path_metadata)
                file_metadata.append((file_path, exif_before, exif_after))
                preview_images.append(convert_image_to_base64(output_path_metadata))
            status_text.value = "\n".join([f"Imagem processada e salva em: {path}" for path in output_paths])
            if len(output_paths) > 0:
                update_preview_gallery()
            open_folder_button.visible = True
            open_folder_button.data = os.path.dirname(output_paths[0])
            result_button.visible = True
            page.update()
        else:
            status_text.value = "Nenhum arquivo selecionado."
        page.update()

    def update_preview_gallery():
        if len(preview_images) > 0:
            preview_gallery.controls = [
                ft.Container(
                    content=ft.Image(src_base64=img, width=200, height=150, fit=ft.ImageFit.CONTAIN),
                    padding=5,
                    border_radius=ft.border_radius.all(10),
                    bgcolor=ft.colors.GREY_200
                ) for img in preview_images
            ]
            preview_gallery.visible = True
            preview_gallery.update()

    def open_folder(e):
        if e.control.data:
            webbrowser.open(f'file://{e.control.data}')

    def show_metadata(e):
        if file_metadata:
            before_metadata_column = ft.Column(scroll='auto')
            after_metadata_column = ft.Column(scroll='auto')
            for file_path, exif_before, exif_after in file_metadata:
                before_metadata_column.controls.append(ft.Text(f"""Arquivo: {file_path}
{format_exif(exif_before)}""", size=12))
                after_metadata_column.controls.append(ft.Text(f"""Arquivo: {file_path}
{format_exif(exif_after)}""", size=12))
            metadata_dialog.content = ft.Row([
                ft.Container(content=before_metadata_column, width=350, padding=10, border_radius=ft.border_radius.all(10), bgcolor=ft.colors.GREY_200),
                ft.VerticalDivider(width=10, color=ft.colors.GREY_400),
                ft.Container(content=after_metadata_column, width=350, padding=10, border_radius=ft.border_radius.all(10), bgcolor=ft.colors.GREY_200)
            ], spacing=20)
            metadata_dialog.open = True
            page.update()

    def format_exif(exif_dict):
        if not exif_dict:
            return "Nenhum metadado"
        formatted_exif = ""
        for ifd, tags in exif_dict.items():
            if tags:
                for tag, value in tags.items():
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-16').strip('\x00')
                        except UnicodeDecodeError:
                            value = value.decode('utf-8', errors='replace')
                    formatted_exif += f"{piexif.TAGS[ifd][tag]['name']}: {value}\n"
        return formatted_exif if formatted_exif else "Nenhum metadado"

    file_picker = ft.FilePicker(on_result=on_files_upload)
    page.overlay.append(file_picker)

    pick_button = ft.ElevatedButton(
        "Selecionar Imagens", 
        icon=ft.icons.IMAGE, 
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), 
        on_click=lambda _: file_picker.pick_files(allow_multiple=True),
        animate_opacity=300,
        animate_scale=300
    )
    open_folder_button = ft.ElevatedButton(
        "Abrir Pasta", 
        icon=ft.icons.FOLDER, 
        visible=False, 
        on_click=open_folder,
        animate_opacity=300,
        animate_scale=300
    )
    result_button = ft.ElevatedButton(
        "Ver Metadados", 
        icon=ft.icons.INFO, 
        visible=False,
        on_click=show_metadata,
        animate_opacity=300,
        animate_scale=300
    )
    preview_image = ft.Image(width=400, height=300, fit=ft.ImageFit.CONTAIN, src="")
    preview_card = ft.Card(
        content=ft.Container(
            content=preview_image,
            padding=10,
            border_radius=ft.border_radius.all(10),
            bgcolor=ft.colors.GREY_200,
            alignment=ft.alignment.center,
            animate=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT)
        ),
        elevation=5
    )
    preview_gallery = ft.GridView(
        controls=[],
        visible=False,
        runs_count=3,
        spacing=10,
        run_spacing=10,
        max_extent=250
    )
    status_text = ft.Text(
        "Selecione uma ou mais imagens para começar.", 
        size=12, 
        weight=ft.FontWeight.NORMAL, 
        color=ft.colors.BLACK87,
        animate_opacity=300
    )
    status_card = ft.Card(
        content=ft.Container(
            content=status_text,
            padding=10,
            border_radius=ft.border_radius.all(10),
            bgcolor=ft.colors.GREY_200,
            alignment=ft.alignment.center,
            animate=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT)
        ),
        elevation=5
    )
    metadata_dialog = ft.AlertDialog(
        title=ft.Text("Metadados"),
        content=ft.Text("Carregando metadados..."),
        actions=[ft.TextButton("Fechar", on_click=lambda e: close_metadata_dialog(e, metadata_dialog))]
    )
    page.overlay.append(metadata_dialog)

    page.add(
        pick_button,
        open_folder_button,
        result_button,
        preview_card,
        preview_gallery,
        status_card,
    )

ft.app(target=main)
