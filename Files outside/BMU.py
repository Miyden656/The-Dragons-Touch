# batch_merge_folder_list_selector.py
# MTG Deck Helper - Folder List Multi-Selector Batch Merger
#
# Purpose:
# Select a parent Outputs folder, then Shift+select or Ctrl+select multiple
# deck folders from a list. The script recursively collects .txt files from
# those selected folders, sorts them by Date Modified, and merges them.
#
# Output is saved in the parent Outputs folder.

from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox


MERGED_FILE_PREFIX = "merged_batch_results"


def is_old_merged_file(path: Path) -> bool:
    """
    Prevents the script from re-merging old merged result files.
    """
    return path.name.lower().startswith(MERGED_FILE_PREFIX.lower())


def format_modified_time(path: Path) -> str:
    modified_timestamp = datetime.fromtimestamp(path.stat().st_mtime)
    return modified_timestamp.strftime("%Y-%m-%d %I:%M:%S %p")


def read_text_file(path: Path) -> str:
    """
    Tries UTF-8 first, then falls back safely if needed.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def collect_txt_files_from_folders(selected_folders: list[Path]) -> list[Path]:
    txt_files = []

    for folder in selected_folders:
        for path in folder.rglob("*.txt"):
            if path.is_file() and not is_old_merged_file(path):
                txt_files.append(path)

    return txt_files


def build_file_header(path: Path, output_folder: Path) -> str:
    try:
        display_path = path.relative_to(output_folder)
    except ValueError:
        display_path = path

    modified_time = format_modified_time(path)

    return (
        "\n"
        + "=" * 100
        + "\n"
        + f"FILE: {display_path}\n"
        + f"MODIFIED: {modified_time}\n"
        + "=" * 100
        + "\n\n"
    )


def merge_txt_files(
    selected_folders: list[Path],
    txt_files: list[Path],
    output_folder: Path
) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_folder / f"{MERGED_FILE_PREFIX}_{timestamp}.txt"

    # Oldest modified files first.
    # Change reverse=False to reverse=True if you want newest first.
    sorted_files = sorted(
        txt_files,
        key=lambda path: (path.stat().st_mtime, str(path).lower()),
        reverse=False
    )

    merged_parts = []

    merged_parts.append(
        "MTG DECK HELPER - MERGED SELECTED FOLDER RESULTS\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}\n"
        f"Output Folder: {output_folder}\n"
        f"Selected Folders: {len(selected_folders)}\n"
        f"Files Merged: {len(sorted_files)}\n"
        "\n"
        "Sort Order: Oldest modified file to newest modified file\n"
        "\n"
        "Selected Folder List:\n"
    )

    for folder in selected_folders:
        merged_parts.append(f"- {folder}\n")

    merged_parts.append("\n")

    for file_path in sorted_files:
        merged_parts.append(build_file_header(file_path, output_folder))
        merged_parts.append(read_text_file(file_path))
        merged_parts.append("\n\n")

    output_file.write_text("".join(merged_parts), encoding="utf-8")

    return output_file


class FolderListSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MTG Deck Helper - Batch Merge Folder Selector")
        self.root.geometry("900x600")

        self.parent_folder: Path | None = None
        self.available_folders: list[Path] = []

        top_frame = tk.Frame(root)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.parent_label = tk.Label(
            top_frame,
            text="No parent Outputs folder selected.",
            anchor="w"
        )
        self.parent_label.pack(side="left", fill="x", expand=True)

        self.choose_parent_button = tk.Button(
            top_frame,
            text="Choose Outputs Folder",
            command=self.choose_parent_folder
        )
        self.choose_parent_button.pack(side="right", padx=5)

        instructions = (
            "Select deck folders below. Use Ctrl+click for individual folders "
            "or Shift+click for a range, then click Merge Selected Folders."
        )

        self.instructions_label = tk.Label(
            root,
            text=instructions,
            anchor="w"
        )
        self.instructions_label.pack(fill="x", padx=10, pady=(0, 5))

        list_frame = tk.Frame(root)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.scrollbar = tk.Scrollbar(list_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.folder_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=self.scrollbar.set,
            exportselection=False
        )
        self.folder_listbox.pack(side="left", fill="both", expand=True)

        self.scrollbar.config(command=self.folder_listbox.yview)

        button_frame = tk.Frame(root)
        button_frame.pack(fill="x", padx=10, pady=10)

        self.select_all_button = tk.Button(
            button_frame,
            text="Select All",
            command=self.select_all
        )
        self.select_all_button.pack(side="left", padx=5)

        self.clear_selection_button = tk.Button(
            button_frame,
            text="Clear Selection",
            command=self.clear_selection
        )
        self.clear_selection_button.pack(side="left", padx=5)

        self.merge_button = tk.Button(
            button_frame,
            text="Merge Selected Folders",
            command=self.merge_selected_folders
        )
        self.merge_button.pack(side="right", padx=5)

        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=root.destroy
        )
        self.cancel_button.pack(side="right", padx=5)

    def choose_parent_folder(self):
        folder = filedialog.askdirectory(
            title="Select the parent Outputs folder"
        )

        if not folder:
            return

        self.parent_folder = Path(folder).resolve()
        self.parent_label.config(text=f"Parent folder: {self.parent_folder}")

        self.load_subfolders()

    def load_subfolders(self):
        self.folder_listbox.delete(0, tk.END)
        self.available_folders.clear()

        if self.parent_folder is None:
            return

        subfolders = [
            path for path in self.parent_folder.iterdir()
            if path.is_dir()
        ]

        subfolders = sorted(subfolders, key=lambda path: path.name.lower())

        for folder in subfolders:
            self.available_folders.append(folder)
            self.folder_listbox.insert(tk.END, folder.name)

        if not subfolders:
            messagebox.showwarning(
                "No Subfolders Found",
                "No deck/output subfolders were found in the selected parent folder."
            )

    def select_all(self):
        self.folder_listbox.select_set(0, tk.END)

    def clear_selection(self):
        self.folder_listbox.selection_clear(0, tk.END)

    def get_selected_folders(self) -> list[Path]:
        selected_indices = self.folder_listbox.curselection()
        return [self.available_folders[index] for index in selected_indices]

    def merge_selected_folders(self):
        if self.parent_folder is None:
            messagebox.showwarning(
                "No Parent Folder Selected",
                "Please choose your parent Outputs folder first."
            )
            return

        selected_folders = self.get_selected_folders()

        if not selected_folders:
            messagebox.showwarning(
                "No Folders Selected",
                "Please select at least one folder to merge."
            )
            return

        txt_files = collect_txt_files_from_folders(selected_folders)

        if not txt_files:
            messagebox.showwarning(
                "No Text Files Found",
                "No .txt files were found in the selected folders."
            )
            return

        output_file = merge_txt_files(
            selected_folders=selected_folders,
            txt_files=txt_files,
            output_folder=self.parent_folder
        )

        messagebox.showinfo(
            "Merge Complete",
            f"Merged {len(txt_files)} text files from "
            f"{len(selected_folders)} selected folders into:\n\n{output_file}"
        )

        print("Merge complete.")
        print(f"Parent folder: {self.parent_folder}")
        print(f"Selected folders: {len(selected_folders)}")
        print(f"Files merged: {len(txt_files)}")
        print(f"Output file: {output_file}")

        self.root.destroy()


def main():
    root = tk.Tk()
    FolderListSelectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()