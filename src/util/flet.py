import flet as ft
from flet import icons


def file_picker_row(
    page: ft.Page, is_directory: bool, label: str
) -> tuple[ft.Row, ft.Text]:
    label = ft.Text(label, size=14)
    item = ft.Text(None, size=14)

    def on_select(e: ft.FilePickerResultEvent) -> None:
        if is_directory:
            item.value = e.path
        else:
            if len(e.files) > 0:
                item.value = e.files[0].path
        item.update()

    picker = ft.FilePicker(
        on_result=on_select,
    )
    button = ft.ElevatedButton(
        text="選択",
        icon=icons.FOLDER_OPEN if is_directory else icons.FILE_OPEN,
        on_click=lambda e: picker.get_directory_path()
        if is_directory
        else picker.pick_files(),
    )
    page.overlay.extend([picker])
    row = ft.Row(
        [
            ft.Row([label, item], spacing=2),
            button,
        ],
        alignment="spaceBetween",
    )

    return row, item
