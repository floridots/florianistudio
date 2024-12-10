import flet as ft
from datetime import datetime
import subprocess
import os
import json
import platform

def get_video_metadata(file_path):
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            return {"error": result.stderr}
        metadata = json.loads(result.stdout)
        return metadata
    except Exception as e:
        return {"error": str(e)}

def update_video_metadata(file_path, new_metadata, output_path, video_filters=None, audio_filters=None):
    try:
        cmd = ['ffmpeg', '-i', file_path]
        if video_filters:
            print(f"Aplicando filtros de vídeo: {video_filters}")
            cmd.extend(['-vf', video_filters])
        
        if audio_filters:
            print(f"Aplicando filtros de áudio: {audio_filters}")  
            cmd.extend(['-af', audio_filters])

        for key, value in new_metadata.items():
            cmd.extend(['-metadata', f'{key}={value}'])
            print(f"Adicionando metadado: {key}={value}")  
        handler_name = "ISO Media file produced by FlorianiStudio Inc."
        cmd.extend(['-metadata:s:v:0', f'handler_name={handler_name}'])
        cmd.extend(['-metadata:s:a:0', f'handler_name={handler_name}'])
        print(f"Adicionando handler_name para vídeo e áudio: {handler_name}")  
        if video_filters or audio_filters:
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac', output_path])
            print(f"Re-encodificando com libx264 e aac para: {output_path}")  
        else:
            cmd.extend(['-codec', 'copy', output_path])
            print(f"Copiando codecs para: {output_path}") 
        
        print(f"Comando FFmpeg: {' '.join(cmd)}") 
        
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        if process.returncode != 0:
            print(f"Erro no FFmpeg: {process.stderr}") 
            return f"Erro: {process.stderr}"
        print("Processo concluído com sucesso.")  
        return "Metadados e conteúdo atualizados com sucesso."
    except Exception as e:
        print(f"Exceção: {str(e)}")  
        return f"Erro ao atualizar metadados: {str(e)}"

def open_folder(file_path):
    folder = os.path.dirname(file_path)
    if platform.system() == "Windows":
        os.startfile(folder)
    elif platform.system() == "Darwin":  
        subprocess.Popen(["open", folder])
    else:  
        subprocess.Popen(["xdg-open", folder])

def generate_output_path(file_path, suffix="_edited"):
    base, ext = os.path.splitext(file_path)
    return f"{base}{suffix}{ext}"

def camouflage_video(file_path, output_path):
    video_filters = (
        "scale='2*trunc(iw*1.01/2)':'2*trunc(ih*1.01/2)',"
        "fps=59.94,"
        "eq=brightness=0.01:saturation=1.01"
    )
    
    audio_filters = "atempo=1.01,asetrate=44110"
    
    new_metadata = {
        "title": "FlorianiStudio",
        "description": "Este é um vídeo camuflado.",
        "artist": "FlorianiStudio",
        "copyright": "© 2024 FlorianiStudio"
    }
    
    return update_video_metadata(
        file_path,
        new_metadata,
        output_path,
        video_filters=video_filters,
        audio_filters=audio_filters
    )

def main(page: ft.Page):
    page.title = "Editor de Metadados de Vídeos MP4"
    page.window.width = 1400
    page.window.height = 900
    page.padding = 20
    page.spacing = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    selected_files = []
    metadata_fields = {}
    video_filters_field = {}
    audio_filters_field = {}
    metadata_display = ft.Column(scroll='auto')
    output_message = ft.Text("Selecione um ou mais vídeos MP4 para editar os metadados.", size=14)
    output_card = ft.Card(
        content=ft.Container(
            content=output_message,
            padding=10,
            border_radius=ft.border_radius.all(10),
            bgcolor=ft.colors.GREY_100,
            alignment=ft.alignment.center
        ),
        elevation=3,
        margin=ft.margin.only(top=10)
    )

    def on_files_upload(e):
        nonlocal selected_files
        try:
            if e.files:
                selected_files = []
                metadata_display.controls.clear()

                for file in e.files:
                    file_path = file.path
                    if not file_path.lower().endswith('.mp4'):
                        output_message.value = f"Arquivo {os.path.basename(file_path)} não é um MP4 válido."
                        continue

                    metadata = get_video_metadata(file_path)
                    if "error" in metadata:
                        output_message.value = f"Erro ao extrair metadados de {os.path.basename(file_path)}: {metadata['error']}"
                        continue

                    selected_files.append(file_path)

                    fields = {}
                    format_tags = metadata.get('format', {}).get('tags', {})
                    format_properties = {k: v for k, v in metadata.get('format', {}).items() if k not in [
                        'tags', 'filename', 'nb_streams', 'nb_programs', 'format_long_name',
                        'start_time', 'duration', 'size', 'bit_rate', 'probe_score']}

                    all_format_tags = format_tags.copy()
                    for prop, value in format_properties.items():
                        all_format_tags[prop] = value

                    for tag, value in all_format_tags.items():
                        fields[tag] = ft.TextField(
                            label=tag.capitalize(),
                            value=str(value),
                            width=400
                        )

                    video_filters_field[file_path] = ft.TextField(
                        label="Filtros de Vídeo (FFmpeg)",
                        hint_text="Exemplo: scale=1280:720,fps=30",
                        width=600
                    )
                    audio_filters_field[file_path] = ft.TextField(
                        label="Filtros de Áudio (FFmpeg)",
                        hint_text="Exemplo: atempo=1.25,volume=0.8",
                        width=600
                    )

                    metadata_display.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Text(f"Arquivo: {os.path.basename(file_path)}", size=16, weight=ft.FontWeight.BOLD),
                                    *[fields[tag] for tag in sorted(fields.keys())],
                                    video_filters_field[file_path],
                                    audio_filters_field[file_path]
                                ], spacing=10),
                                padding=10,
                                border_radius=ft.border_radius.all(10),
                                bgcolor=ft.colors.WHITE,
                            ),
                            elevation=3,
                            margin=ft.margin.only(bottom=20)
                        )
                    )

                    metadata_fields[file_path] = fields

                if selected_files:
                    output_message.value = f"{len(selected_files)} arquivo(s) selecionado(s) para edição."
                else:
                    output_message.value = "Nenhum arquivo válido selecionado."

                update_buttons()
                page.update()
            else:
                output_message.value = "Nenhum arquivo selecionado."
                update_buttons()
                page.update()
        except Exception as err:
            output_message.value = f"Erro ao processar os arquivos: {str(err)}"
            page.update()

    def save_metadata(e):
        try:
            if not selected_files:
                output_message.value = "Nenhum arquivo selecionado para salvar."
                page.update()
                return

            for file_path in selected_files:
                fields = metadata_fields.get(file_path, {})
                new_metadata = {}

                for tag, field in fields.items():
                    if field.value.strip():
                        new_metadata[tag] = field.value.strip()

                video_filters = video_filters_field[file_path].value.strip()
                video_filters = video_filters if video_filters else None

                audio_filters = audio_filters_field[file_path].value.strip()
                audio_filters = audio_filters if audio_filters else None

                output_path = generate_output_path(file_path)

                result = update_video_metadata(
                    file_path,
                    new_metadata,
                    output_path,
                    video_filters=video_filters,
                    audio_filters=audio_filters
                )
                output_message.value = result

            page.update()
        except Exception as err:
            output_message.value = f"Erro ao salvar metadados: {str(err)}"
            page.update()

    def show_metadata(e):
        try:
            if not selected_files:
                output_message.value = "Nenhum arquivo selecionado para mostrar metadados."
                page.update()
                return

            metadata_info = ft.Column()

            for file_path in selected_files:
                metadata = get_video_metadata(file_path)
                if "error" in metadata:
                    metadata_info.controls.append(ft.Text(f"Erro em {os.path.basename(file_path)}: {metadata['error']}", color=ft.colors.RED))
                    continue

                format_tags = metadata.get('format', {}).get('tags', {})
                format_properties = {k: v for k, v in metadata.get('format', {}).items() if k not in [
                    'tags', 'filename', 'nb_streams', 'nb_programs', 'format_long_name',
                    'start_time', 'duration', 'size', 'bit_rate', 'probe_score']}

                all_format_tags = format_tags.copy()
                for prop, value in format_properties.items():
                    all_format_tags[prop] = value

                metadata_info.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(f"Arquivo: {os.path.basename(file_path)}", size=16, weight=ft.FontWeight.BOLD),
                                *[ft.Text(f"{k.capitalize()}: {v}") for k, v in sorted(all_format_tags.items())]
                            ], spacing=5),
                            padding=10,
                            border_radius=ft.border_radius.all(10),
                            bgcolor=ft.colors.WHITE,
                        ),
                        elevation=2,
                        margin=ft.margin.only(bottom=15)
                    )
                )

            metadata_dialog.content = ft.Container(
                content=metadata_info,
                width=1200,
                height=700
            )
            metadata_dialog.open = True
            page.update()
        except Exception as err:
            output_message.value = f"Erro ao mostrar metadados: {str(err)}"
            page.update()

    def close_metadata_dialog(e, dialog):
        dialog.open = False
        page.update()

    def camouflage_video_action(e):
        try:
            if not selected_files:
                output_message.value = "Nenhum arquivo selecionado para camuflar."
                page.update()
                return

            for file_path in selected_files:
                base, ext = os.path.splitext(file_path)
                output_path = f"{base}_camuflage{ext}"

                result = camouflage_video(file_path, output_path)
                output_message.value = f"{os.path.basename(file_path)}: {result}"

            page.update()
        except Exception as err:
            output_message.value = f"Erro ao camuflar vídeo: {str(err)}"
            page.update()

    file_picker = ft.FilePicker(on_result=on_files_upload)
    page.overlay.append(file_picker)

    pick_button = ft.ElevatedButton(
        "Selecionar Vídeos MP4",
        icon=ft.icons.VIDEO_LIBRARY,
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=True,
            file_type=ft.FilePickerFileType.VIDEO
        )
    )
    save_button = ft.ElevatedButton(
        "Salvar Metadados e Alterar Conteúdo",
        icon=ft.icons.SAVE,
        on_click=save_metadata,
        disabled=True
    )
    show_metadata_button = ft.ElevatedButton(
        "Mostrar Metadados",
        icon=ft.icons.INFO,
        on_click=show_metadata,
        disabled=True
    )
    open_folder_button = ft.ElevatedButton(
        "Abrir Pasta do Arquivo",
        icon=ft.icons.FOLDER_OPEN,
        on_click=lambda e: open_folder(selected_files[0]) if selected_files else None,
        disabled=True
    )
    camouflage_button = ft.ElevatedButton(
        "Camuflar Vídeo",
        icon=ft.icons.COLOR_LENS,
        on_click=camouflage_video_action,
        disabled=True
    )

    def update_buttons():
        if selected_files:
            save_button.disabled = False
            show_metadata_button.disabled = False
            open_folder_button.disabled = False
            camouflage_button.disabled = False
        else:
            save_button.disabled = True
            show_metadata_button.disabled = True
            open_folder_button.disabled = True
            camouflage_button.disabled = True
        page.update()

    metadata_dialog = ft.AlertDialog(
        title=ft.Text("Metadados dos Arquivos MP4"),
        content=ft.Container(),
        actions=[
            ft.TextButton("Fechar", on_click=lambda e: close_metadata_dialog(e, metadata_dialog))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        modal=True
    )
    page.overlay.append(metadata_dialog)

    page.add(
        ft.Row(
            controls=[pick_button, save_button, show_metadata_button, open_folder_button, camouflage_button],
            spacing=10,
            alignment=ft.MainAxisAlignment.START
        ),
        metadata_display,
        output_card
    )

ft.app(target=main)
