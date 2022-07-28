# ProbabilisticMelodyGenerator
A framework for generating melodies based on Indian classical ragas using Finite Automata. 

## Installation Guide ##

Setup the requirements and load the audio font:

```bash
sudo sh install.sh
```
## Usage

The pipeline requires a probability distribution trained called a finite automaton or a state machine. For the sake of demonstration, let us use an example data file `yaman.dat`
```bash
python train.py --data_path=data/yaman.dat
```
The trained automata is saved in the the `models` directory as `yaman.aut`. We will use it to generate the midi file and the audio wav file. We will also specify the illegal notes that are not used in the raga, i.e., r, g, M, d, n . (For more options, use `--help`.)
```bash
python generate.py --model_path=models/yaman.aut -x r g M d n
```
The output midi and wav files are saved in the `output` directory.
