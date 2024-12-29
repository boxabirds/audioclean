# MOV Cleaner

This tool processes MOV video files to remove silent parts and optionally enhance the audio. It uses Silero VAD (Voice Activity Detection) to identify speech segments and replaces non-speech parts with silence.

**Note:** This project uses `pipenv` for managing dependencies and the Python version. Ensure you have `pipenv` installed before proceeding. You can install it using:

```bash
pip install pipenv
```

## Prerequisites

Before using this tool, ensure you have the following installed:

* **Python 3.7 or higher:** This tool is developed and tested with Python 3.
* **pipenv:** For managing project dependencies.
* **ffmpeg:**  Required for audio extraction and applying the high-pass filter. You can usually install it using your system's package manager (e.g., `sudo apt-get install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on macOS).

## Installation

1. **Clone the repository (or download the script):**

   If you have the script in a file, navigate to the directory containing the script in your terminal.

2. **Create a virtual environment and install dependencies:**

   Navigate to the directory containing the script in your terminal and run:

   ```bash
   pipenv install
   ```

   This command reads the `Pipfile` (which `pipenv` creates based on the imports in the script) and installs all necessary libraries, including `torch`, `pydub`, `moviepy`, `numpy`, `silero_vad`, and `scipy`.

## Usage

To run the script, activate the virtual environment first:

```bash
pipenv shell
```

Then, execute the script with the required arguments:

```bash
python your_script_name.py <input_mov_file> [options]
```

Replace `<input_mov_file>` with the path to your MOV video file.

### Options

* **`input_mov_file`**:  The path to the input MOV video file you want to process. This is a required argument.

* **`--filter [FREQUENCY]`**:  Applies a high-pass filter to the audio.
    * If you use `--filter` without specifying a frequency, it defaults to 250 Hz.
    * To specify a frequency, use `--filter <frequency_in_Hz>`. It's recommended to keep the frequency between 100 and 2000 Hz.

    ```bash
    python your_script_name.py input.mov --filter
    ```

    ```bash
    python your_script_name.py input.mov --filter 300
    ```

* **`--punch`**: Applies a compressor effect to the audio to make the speech more prominent.

    ```bash
    python your_script_name.py input.mov --punch
    ```

### Examples

* **Basic cleaning (remove silence):**

   ```bash
   python your_script_name.py my_video.mov
   ```

   This will create a new file named `my_video-cleaned.mov` in the same directory as the input file.

* **Cleaning with a high-pass filter at the default frequency (250 Hz):**

   ```bash
   python your_script_name.py my_video.mov --filter
   ```

* **Cleaning with a high-pass filter at 400 Hz:**

   ```bash
   python your_script_name.py my_video.mov --filter 400
   ```

* **Cleaning and applying the compressor:**

   ```bash
   python your_script_name.py my_video.mov --punch
   ```

* **Cleaning, applying a high-pass filter, and the compressor:**

   ```bash
   python your_script_name.py my_video.mov --filter 350 --punch
   ```

### Output

The processed video file will be saved in the same directory as the input file, with `-cleaned` appended to the original filename (before the extension). For example, if the input file is `my_video.mov`, the output file will be `my_video-cleaned.mov`.

## Note on Pipenv

This tool utilizes `pipenv` for managing its dependencies and ensuring a consistent Python environment. This means that the specific versions of the libraries used by this tool are tracked in the `Pipfile.lock` file. By using `pipenv`, you can easily recreate the exact environment used for development, avoiding potential compatibility issues.

To exit the `pipenv` shell, simply type `exit` in your terminal.
```
