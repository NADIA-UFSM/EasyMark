# EasyMark

EasyMark is an offline image annotation software developed by students of the Federal University of Santa Maria, at the Data Science and Artificial Intelligence Center (NADIA). Programmed in Python and utilizing the Tkinter UI framework, EasyMark allows the user to annotate large batches of images and export these annotations in a proper format for AI object detection training. The tool contains manual, semi-automatic and fully automatic annotation features depending on the user's needs.

## Index
* [Pré-requisitos](#pré-requisitos)
* [Instalation](#instalation)
* [How to Use](#how-to-use)
* [Contact](#contact)

## Pré-requisitos

As configurações das máquinas em que o repositório foi desenvolvido e testado encontram-se na tabela abaixo:

| Configuração        | Valor                        |
|---------------------|------------------------------|
| Sistema operacional | Ubuntu 22.04.4 LTS (64 bits) |
| Processador         | Intel Core i7-10700F         |
| Memória RAM         | 16GB                         |
| Necessita rede?     | Não                          |

| Configuração        | Valor                        |
|---------------------|------------------------------|
| Sistema operacional | Windows 10 Pro               |
| Processador         | AMD Ryzen 3 3200G            |
| Memória RAM         | 16GB                         |
| Necessita rede?     | Não                          |

## Instalation
Installation can be done by cloning the repository and installing the dependencies in a [**Python>=3.13.0**](https://www.python.org/) environment

```bash
# Clone the EasyMark repository
git clone https://github.com/NADIA-UFSM/EasyMark.git

# Navigate to the cloned directory
cd EasyMark

# Create and activate a virtual environment
python -m venv .venv
.venv\scripts\acivate # Windows systems
source .venv\bin\activate # Linux systems

# Install required packages
pip install -r requirements.txt
```

## How To Use

Execute the `main.py` file via terminal:
```bash
cd EasyMark

.venv\scripts\acivate # Windows systems
source .venv\bin\activate # Linux systems

python main.py
```
Once executed a graphical interface will appear.

### Starting a new project

On the top bar, open a new project by clicking File > Open > New Project or pressing `Ctrl + N`.The user will be prompted to choose between a manual or semi-automatic project and a directory (folder of images) to be loaded for the project. 

### Annotating images

Before annotating, the user must create at least one object category. The option is available on the side bar, allowing the user to name and choose a color for each new category (without repeating names). The user can annotate the images utilizing the cursor. Navigation can be done either with the arrows at the bottom or utilizing the arrow keys.

- Manual annotation: The user can highlight each desired object by drawing either a bounding box, oriented bounding box or a polygon, option selected on the floating tool bar on the image.
- Semi-automatic annotation: The user can place "seeds" over each desired object.

Saving the project canbe done via the top bar on File > Save > Save Project or pressing `Ctrl + S`. The project will be saved as <project_name>.json.

### Loading a project

On the top bar, the user can load a project on File > Open > Continue Project or pressing `Ctrl + O`. The user will be prompted to select a <project_name>.json, the stored categories and annotations will be loaded alongisde the assigned image folder.

### Automated Annotation

This feature allows the use of AI models to infer the annotations automatically to accelerate the dataset creation process. The feature can be access on the top bar, on Tools > Automattic Annotation.

A pop up window will appear with settings for the automated process. The user can choose between the default FastSam model or a pre-trained personal model (currently oly supports YOLO models).
The FastSAM model is used for semi-automatic annotation, as such, it is required to load a semi-automatic project file to function.
The result will be a new project file set to manual annotation, to allow fixes and adjustments.

### Exporting a project

To export a project as a dataset for model training, on the top bar go to file > Export Project or press `Ctrl + E`.
A pop up window will appear with settings for dataset format (currently only supports the YOLOv8 dataset format), startification, partition size and more.
The result will be a dataset with a .yaml file and the correct file structure for use.

## Contact

For bug reports or feature requests, contact the dev at [samuel.vargas@acad.ufsm.br](samuel.vargas@acad.ufsm.br)
