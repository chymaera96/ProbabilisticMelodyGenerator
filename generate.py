import music21
import numpy as np
import pickle
import random
import os
import sys
import uuid
import argparse
import subprocess

parser = argparse.ArgumentParser(description='Generate Melody from Automata')
parser.add_argument('--model_path', default='', type=str, metavar='PATH',
                    help='path containing trained automaton')
parser.add_argument('--note_duration', default=0.6, type=float,
                    help='duration of a single note')
parser.add_argument('--n_cycles', default=5, type=float,
                    help='number of measures / beat cycles')
parser.add_argument('-x','--xnotes', '--names-list', nargs='+', default=[],
                    help='list of restricted notes')
parser.add_argument('--save_audio', default=True, type=bool,
                    help='If True, produced a wav file from the midi')

root = os.path.abspath(os.getcwd())

def translate_notation(swaras):
    '''
    This translates the notes in the data file to western scales.
    '''
    hindi = ['S',r'r','R','g','G','M','m','P','d','D','n','N']
    english = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    trans =  dict(zip(hindi, english))
    note = []
    for s in swaras:
        if s!=',':
            octave = s[1]
            note.append(trans[s[0]]+octave)
        else:
            note.append(s)
    return note

def create_noteset():
    '''
    This creates the set of notes to chose from. "," indicates 
    that the previous note is to be sustained for one beat.
    '''
    noteset = []
    hindi = ['S',r'r','R','g','G','M','m','P','d','D','n','N']
    for ix in range(3,6):
        for n in hindi:
            nt = n + str(ix)
            noteset.append(nt)
    noteset.append(',')
    return noteset

def compute_legal_notes(unotes, illegal_notes):
    noteset = []
    for ix in range(3,6):
        for n in illegal_notes:
            nt = n + str(ix)
            noteset.append(nt)

    legal_notes = [n for n in unotes if n not in noteset]
    return legal_notes


def generate_midi_from_automata(
    transition_probs,
    note_duration = 0.7,
    num_beat_cycles = 5,
    alankar_density = 2,
    taal=16,
    illegal_notes=[]):

    """
    Function for generating midi score from trained automata

    Parameters
    ----------
    transition_probs : ndarray
        A 2-D array containing the transition probabilities between 
        all permutations of notes (trained using train.py)

    note_duration: float
        the duration of a one note (in seconds)
        
    num_beat_cycles : int
        Number of measures or beat cycles in the score
    
    alankar density : int
        Number of shorter notes in a duration of a single note. This simulates
        the "gamaka" or "harkat" in a melofy

    taal : int
        number of beats in a cycle
    
    illegal_notes : list
        a list of notes which are not allowed for the particular raga. For
        example - ['r','g','M','d','n'] in Raga Bilawal.
    
    Returns
    -------
    MIDI score: music21 object

    """

    unotes = translate_notation(create_noteset())
    centre = int((len(unotes)-1)/3) 

    prev_swar_ind = centre  # Initialize the automata with the tonic in the middle octave
    part = music21.stream.Part(id='flute')
    part.append(music21.instrument.Flute())
    prev_note = music21.note.Note(unotes[prev_swar_ind])
    backup_swar_ind = prev_swar_ind

    legal_notes = compute_legal_notes(unotes=create_noteset(), illegal_notes=illegal_notes)
    R1_notes = translate_notation(legal_notes)
    print("List of legal notes")
    print(R1_notes)

    for cycle in range(num_beat_cycles):
        notes_list = []
        measure = music21.stream.Measure(number=1)
        # First measure starts with the centre note 
        if cycle == 0:
            note = music21.note.Note(unotes[centre])
            note.duration.quarterLength = note_duration
            measure.append(note)
        else:
            for taal_num in range(taal):
                while np.sum(transition_probs[prev_swar_ind,:]) < 1.0:
                    if prev_swar_ind > centre:
                        prev_swar_ind -= 1
                    else:
                        prev_swar_ind += 1
                swar_ind = np.random.choice(np.arange(len(unotes)),p=transition_probs[prev_swar_ind,:])

                # Random seed for the alankar
                seed = random.uniform(-1, 1)
                if seed < 0 and taal_num != 0:
                    notes_list[-1].duration.quarterLength = note_duration/alankar_density

                    for ix in np.arange(note_duration/alankar_density,note_duration,note_duration/alankar_density):
                        if unotes[swar_ind] == ',':
                            notes_list[-1].duration.quarterLength += note_duration/alankar_density
                        else:
                            # insert a note with duration alankar_density
                            this_note = music21.note.Note(unotes[swar_ind])
                            this_note.duration.quarterLength = note_duration/alankar_density
                            notes_list.append(this_note)

                            # update previous swar to fill in the next note in alankar
                            prev_swar_ind = swar_ind
                            prev_note = this_note

                            while unotes[swar_ind] not in R1_notes:
                                if swar_ind > centre:
                                    swar_ind -= 1
                                else:
                                    swar_ind += 1
                            alankar_ind = R1_notes.index(unotes[swar_ind])
                            # get index for next note in alankar
                            if seed < 0.5:
                                alankar_ind += 1
                            else:
                                alankar_ind -= 1

                            if alankar_ind > len(R1_notes): 
                                alankar_ind -= 2
                            if alankar_ind < 0: 
                                alankar_ind += 2
                
                            swar_ind = unotes.index(R1_notes[alankar_ind])
        
                else:
                    if unotes[swar_ind] == ',' and taal_num==0:
                        # print("Wrong starting note!")
                        while unotes[swar_ind] == ',':
                            swar_ind = np.random.choice(np.arange(len(unotes)),p=transition_probs[backup_swar_ind,:])

                # extend note duration if current index denotes a ','
                if unotes[swar_ind] == ',':
                    notes_list[-1].duration.quarterLength += note_duration
                else:
                    # create a note object for one quarterLength
                    this_note = music21.note.Note(unotes[swar_ind])
                    this_note.duration.quarterLength = note_duration

                    # add it to the list
                    notes_list.append(this_note)
                    # update note and swara index for next iteration
                    backup_swar_ind = prev_swar_ind
                    prev_swar_ind = swar_ind
                    prev_note = this_note

        for note in notes_list:
            measure.append(note)

        # add measure to part
        part.append(measure)

    # create an empty score
    simulation = music21.stream.Score()

    # add the part to it
    simulation.append(part)

    return simulation


def main():
    args = parser.parse_args()
    model_path = args.model_path

    with open(os.path.join(root,model_path), "rb") as fp:  
        transition_probs = pickle.load(fp) 
    
    simulation = generate_midi_from_automata(transition_probs,
    note_duration = args.note_duration,
    num_beat_cycles = args.n_cycles,
    illegal_notes=args.xnotes)

    filename = "output/sim"+str(uuid.uuid4())+".mid"
    fp = simulation.write('midi', fp=filename)
    
    if args.save_audio:
        audio_path = filename.split('.')[0] + '.wav'
        cmd = f"fluidsynth -ni font.sf2 {filename} -F {audio_path} -r 22050"
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()

if __name__ == '__main__':
    main()