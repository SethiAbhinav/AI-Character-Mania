import streamlit as st
from story_processing import extract_story, extract_dialogues, is_dialogue_format
from voice_handling import play_dialogues
from asr import get_user_voice_input, whisper_asr, generate_ai_response
from dotenv import load_dotenv
from elevenlabs import set_api_key, generate, play, save
from audio_recorder_streamlit import audio_recorder
import os
import json
from time import sleep
import base64

load_dotenv()

# Put your API key in a separate configuration file or environment variable
set_api_key(os.getenv("ELEVEN_API_KEY"))

def set_bg_hack(main_bg):
    '''
    A function to unpack an image from root folder and set as bg.
 
    Returns
    -------
    The background.
    '''
    # set bg name
    main_bg_ext = "png"
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover
         }}

         #root .block-container {{
             background: rgba(83, 163, 161, 0.9);
             border-radius: 10px;
             margin: 10px;
             padding: 10px;
        }}
         </style>
         """,
         unsafe_allow_html=True
     )

def delete_files(directory, files_to_keep):
            # List all files in the directory
            files = os.listdir(directory)

            # Loop over the files
            for file in files:
                # Construct full file path
                file_path = os.path.join(directory, file)

                # Check if this is the file we want to keep
                if file not in files_to_keep and os.path.isfile(file_path):
                    # This is not the file we want to keep, delete it
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")

def main():
    set_bg_hack('assets/Background1.png')
    st.title('Magical Voiceover App')
    print(1)
    if 'script' not in st.session_state:
        st.session_state.script = ''

    # Get the script from the user
    st.session_state.story_title = st.text_input("What is the title of the story?")
    st.session_state.script = st.text_area('Enter the script:', st.session_state.script)
    print(2)
    # Show a button for the user to start the magic
    if st.button('Magical Voiceover Time'):
        progress_bar = st.progress(0)
        
        # Process the script
        if is_dialogue_format(st.session_state.script):
            story_metadata = extract_dialogues(st.session_state.script)
            

        else:
            story_metadata = extract_story(st.session_state.script)
            # print(story_metadata['Dialogues'])
            # print(type(story_metadata['Dialogues']))

        progress_bar.progress(20)

        all_characters = []
        for role in story_metadata['Dialogues']:
            # print(role)
            try:
                all_characters.append(role['Character'].strip())
            except:
                all_characters.append(story_metadata['Dialogues'][role])
        all_characters = list(set(all_characters))
        story_metadata['Characters'] = ','.join(all_characters)
        # print(story_metadata)

        progress_bar.progress(35)
        
        # Generate and play voices
        audio_files, character_voices = play_dialogues(story_metadata)
        # st.write(audio_files)
        progress_bar.progress(60)
        print(3)
        st.title(st.session_state.story_title)
        for audio_file_path, role in zip(audio_files, story_metadata['Dialogues']):
            # print(role)
            audio_file = open(audio_file_path, 'rb')
            audio_bytes = audio_file.read()
            character_name = audio_file_path.split('.wav')[0].split('_')[-1]
            st.markdown(f":sparkles: **{character_name}**")
            try:
                st.markdown(f"_{role['Dialogue']}_")
            except: 
                st.markdown(story_metadata['Dialogues'][role])
            st.audio(audio_bytes, format='audio/wav')
        print(4)
        st.write("**Generating follow-up question...**")
        sleep(2) # yes, it's just a sleep call. It shows potential to add another API call to generate relevant questions basis the content of the book.
        st.write('**Generation complete!**')
        if st.session_state.story_title :
            question = f"What did you like about the story? What did you learn from it? - You can start with your response when you like... Just click the button below. -- Hope you had a great time! Listening to the story titled -- {st.session_state.story_title}"
        else:
            question = f"What did you like about the story? What did you learn from it? - You can start with your response when you like... Just click the button below. -- Hope you had a great time!"
        AI_QUESTION = generate(text = question,
                        voice = 'Bella',
                        model = 'eleven_multilingual_v1')
        save(AI_QUESTION, './voices/ai_question.wav')  

        print(5)

        with st.expander("Some things to Ponder upon..."):
            question_text = "\n Note: I request you to please keep your reply short. To begin, click the mic button below. It will take a while for the response to be generated."
            AI_QUESTION_file = open('./voices/ai_question.wav', 'rb')
            AI_QUESTION_bytes = AI_QUESTION_file.read()
            st.audio(AI_QUESTION_bytes, format='audio/wav')
            st.write(question_text)
        
        progress_bar.progress(100)
        
        print(6)
    try:
        user_response_text = ''

        # Record or upload audio
        audio_bytes = audio_recorder(energy_threshold=(-1.0, 1.0), pause_threshold=10.0)

        # Write the recorded audio to a file if it exists
        if audio_bytes:
            with open('voices/user_response.wav', 'wb') as audio_file:
                audio_file.write(audio_bytes)
        print(7)
        if os.path.exists('./voices/user_response.wav'):
            print(8)

            user_response_text = whisper_asr(audio_file_path)
            print('asr passed')
            ai_response = generate_ai_response(user_response_text)
            response_audio_path = 'voices/ai_response.wav'
            response_audio = generate(voice = 'Bella', text = ai_response)
            play(response_audio)
            save(response_audio, response_audio_path)
            print('read passed')
            response_audio_file = open(response_audio_path, 'rb')
            response_audio_bytes = response_audio_file.read()
            with st.expander('Closing Remarks'):
                st.audio(response_audio_bytes, format='audio/wav')
                st.write(ai_response)
            # Directory where the files are located
            directory = "voices/"
            # Name of the file you want to keep
            files_to_keep = ["ai_question.wav", "user_response.wav", "ai_response.wav"]
            # Call the function to delete files
            delete_files(directory, files_to_keep)
        else:
            print(9)

            user_response_text = whisper_asr('./voices/user_response.wav')
            ai_response = generate_ai_response(user_response_text)
            response_audio_path = 'voices/ai_response.wav'
            response_audio = generate(voice = 'Bella', text = ai_response)
            save(response_audio, response_audio_path)

            response_audio_file = open(response_audio_path, 'rb')
            response_audio_bytes = response_audio_file.read()
            with st.expander('Closing Remarks'):
                st.audio(response_audio_bytes, format='audio/wav')
                st.write(ai_response)
        
            # Directory where the files are located
            directory = "voices/"
            # Name of the file you want to keep
            files_to_keep = ["ai_question.wav", "user_response.wav", "ai_response.wav"]
            # Call the function to delete files
            delete_files(directory, files_to_keep)

    except:
        pass
    print(11)

if __name__ == '__main__':
    main()