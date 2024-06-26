from rendering.start_render import render
from audio.audio_generation import *
from nlp.nlp_manager import *
from mesh_generation.generator import *
from rendering.momask_utils import *
import spacy
import json
from transformers import pipeline

prompt = input("Please enter your story (End with a period): ")
#voiceover_enabled = input("Would you like a voice over? (Y/n)") == 'Y'
nlp = spacy.load("en_core_web_sm")
doc = nlp(prompt)

#sentence container
sentences = []
# current sentence
current = []

# organize sentences
for token in doc:
    if str(token) == ".":
        sentences.append(current)
        current = []
    else:
        current.append(token)


# the threshold (between 0 and 1) which determines whether an action should be preformed
ACTION_THRESHOLD = 0.75
CHARACTER_THRESHOLD = 0.9

# vars for json
timeline = {}
next_frame = 1
all_characters = []

# possible object to generate
#objs = find_possible_objects(prompt)

#for obj in objs:
    #generate_object(obj)

# determines if an animation is needed or not
classifier = pipeline("zero-shot-classification")

for i, sentence_tokens in enumerate(sentences):
    # get setence (without period)
    sentence = ' '.join([str(token) for token in sentence_tokens])
    
    # estimates sentence length based on an equation
    sequence_length = estimate_sentence_length(sentence)
    
    #generate background and speech audio based on the sentence
    background_audio_path = generate_audio(i, sentence, sequence_length)
    tts_audio_path = tts(i, sentence)
    
    # uses a transformer
    action_score = classifier(str(sentence), ["physical action"])["scores"][0]
    actions = [str(token.lemma_) for token in sentence_tokens if token.pos_ == "VERB" and action_score > ACTION_THRESHOLD]
    characters = [str(token) for token in sentence_tokens if token.pos_ == "PROPN" and classifier(str(token), ["person"])["scores"][0] > CHARACTER_THRESHOLD]

    character_dict = {}
    if len(characters) != 0:
        for index, character in enumerate(characters):
            if character not in all_characters:
                all_characters.append(character)
            else:
                all_characters.remove(character)
                all_characters.append(character)
            if len(actions) != 0 and index < len(actions):
                character_dict[character.lower()] = {'animation':actions[index]}
            else:
                character_dict[character.lower()] = {'animation': 'idle'}
            
    elif len(actions) != 0:
        character_dict[all_characters[-1].lower()] = {'animation':actions[0]}
    else:
        character_dict[all_characters[-1].lower()] = {'animation':'idle'}
 
    # saves the frames
    timeline[str(next_frame)] = {'audio_paths': [background_audio_path, tts_audio_path], 'characters': character_dict}
    next_frame += sequence_length * 30
   
timeline['end_frame'] = next_frame
with open('frame_data.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=4)
render()

