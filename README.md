# dance

:construction: This repo is ***Work-in-Progress (WIP) to clean up the codes***, please contact the author at `liuzichen@u.nus.edu` if you'd like to get the weights / raw codes as soon as possible!! :)

|![](./assets/pipeline.png)|![](assets/demo.gif)|
|:---:|:---:|
|*DANCE's Pipeline*| *Illustration* |

## Get started
1. Prepare the environment (the scripts are just examples)
   - gcc & g++ ≥ 5
   - Python 3.6.8 (developed & tested on this version)
     - `conda create --name dance python==3.6.8`
     - `conda deactivate && conda activate dance`
   - PyTorch 1.5.1 with CUDA 10.1
     - `conda install pytorch==1.5.1 torchvision==0.6.1 cudatoolkit=10.1 -c pytorch`
2. Clone this project and install framework / package dependency
   - `git clone https://github.com/lkevinzc/dance && cd dance && pip install -r requirements && cd ..`
   - `git clone https://github.com/facebookresearch/detectron2.git && cd detectron2 && git checkout 1a7daee064eeca2d7fddce4ba74b74183ba1d4a0`
   - `python -m pip install -e .`
   - `cd core/layers/extreme_utils && export CUDA_HOME="/usr/local/cuda-9.0" && python setup.py build_ext --inplace`
3. Prepare dataset
   - Download form [COCO official website]()
   - put it at `datasets/coco`
4. Evaluate pre-trained model
   - Download from [here]()
   - put it at `output/r50_1x`
   - evaluate: 
```bash
python train_net.py --config-file configs/Dance_R_50_3x.yaml --eval-only MODEL.WEIGHTS ./output/r50_3x/model_final.pth
```