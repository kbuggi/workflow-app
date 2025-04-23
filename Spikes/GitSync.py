import os
import git
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

#TODO - this is quick and easy for .jsons & they're not too big - if recipes/workflows had resource files like sounds/images/videos it would be possible to store them in a diff repo and download them based on their etag (either we store the etag and check if it's changed or the recipe knows the etag and we check if we have it or that's the one in github). folder/git and folder/library; maybe each recipe would just have a .gz containing all their stuff and we pull that.



class GitSyncThread(QThread):
    # Define a signal to update the UI with status messages
    update_signal = pyqtSignal(str)

    def __init__(self, repo_url, local_folder):
        super().__init__()
        self.repo_url = repo_url
        self.local_folder = local_folder

    def run(self):
        """This method runs in the background thread."""
        try:
            # If the directory doesn't exist or is not a valid Git repository, clone the repository
            if not os.path.exists(self.local_folder):
                msg = f"Cloning repository {self.repo_url}..."
                print(msg)
                self.update_signal.emit(msg)
                # Clone the repository into the specified local folder
                git.Repo.clone_from(self.repo_url, self.local_folder)
                msg = f"Repository {self.repo_url} cloned successfully"
                print(msg)
                self.update_signal.emit(msg)
            else:
                try:
                    # Check if the folder is a valid Git repository
                    repo = git.Repo(self.local_folder)  # This raises an error if it's not a valid Git repo
                    origin = repo.remotes.origin
                    msg = f"Checking for updates to {self.repo_url}..."
                    print(msg)
                    self.update_signal.emit(msg)
                    result =origin.pull()  # Pull the latest changes from the remote repository
                    print("Pull completed. Details:")
                    for info in result:
                        print(f"Ref: {info.ref.name}")  # The branch or ref that was updated
                        print(f"Commit: {info.commit}")  # The commit hash after the pull
                        print(f"Flags: {info.flags}")  # Flags indicating the type of update
                    changed_files = repo.git.diff('HEAD~1', name_only=True).splitlines()
                    print(f"Number of files changed: {len(changed_files)}")
                    print("Changed files:")
                    for file in changed_files:
                        print(file)
                    msg = f"Repository {self.repo_url} synched;  {len(changed_files)} file(s) changed."
                    print(msg)
                    self.update_signal.emit(msg)
                   

                except git.exc.InvalidGitRepositoryError:
                    # If the folder isn't a valid Git repository, clone it
                    msg = f"Invalid repository. Cloning new repo for {self.repo_url} ..."
                    print(msg)
                    self.update_signal.emit(msg)
                    git.Repo.clone_from(self.repo_url, self.local_folder)
                    msg = f"Repository {self.repo_url} cloned successfully."
                    print(msg)
                    self.update_signal.emit(msg)
        except Exception as e:
            print(f"Error: {str(e)}")
            self.update_signal.emit(f"Error: {str(e)}")


class ConfigSyncApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration Sync")
        self.setGeometry(100, 100, 400, 300)

        # Initialize the UI
        self.initUI()

        # Local folder where configuration files will be stored
        self.config_folder = '/tmp/GitSync/Config'  # Update this path as needed
        self.repo_url = 'https://github.com/Droidzzzio/speak' 

        print (f"Config folder: {self.config_folder}")
        print (f"Repo URL: {self.repo_url}")


    def initUI(self):
        """Set up the UI elements."""
        # Button to manually check for updates
        check_update_btn = QPushButton('Check for Updates', self)
        check_update_btn.clicked.connect(self.start_sync)

        # Label to display the status of the sync
        self.status_label = QLabel('Status: Waiting for action...', self)

        # Layout to arrange widgets
        layout = QVBoxLayout()
        layout.addWidget(check_update_btn)
        layout.addWidget(self.status_label)

        container = QWidget(self)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_sync(self):
        """Start the sync operation in a separate thread."""
        self.status_label.setText("Status: Syncing...")
        # Create and start the background thread
        self.git_thread = GitSyncThread(self.repo_url, self.config_folder)
        self.git_thread.update_signal.connect(self.update_status)
        self.git_thread.start()

    def update_status(self, message):
        """Update the status label with messages from the background thread."""
        self.status_label.setText(f"Status: {message}")


if __name__ == "__main__":
    app = QApplication([])
    window = ConfigSyncApp()
    window.show()
    app.exec()
