import json
import os
import hashlib

def process_chat_files(input_dir, output_dir):
    """
    Processes JSON chat files from an input directory, extracts user-model conversation pairs,
    and saves them as individual, sorted, and unique markdown files in an output directory.

    Args:
        input_dir (str): The path to the directory containing the original chat JSON files.
        output_dir (str): The path to the directory where processed chat pairs will be saved.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    seen_hashes = set()

    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            input_filepath = os.path.join(input_dir, filename)
            chat_name = os.path.splitext(filename)[0]

            with open(input_filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from {filename}. Skipping.")
                    continue

            # In the Google AI Studio export format, the conversation is in chunkedPrompt.chunks
            if "chunkedPrompt" in data and "chunks" in data["chunkedPrompt"]:
                chunks = data["chunkedPrompt"]["chunks"]
                pair_counter = 1
                
                # We iterate through the chunks to find user/model pairs
                for i in range(len(chunks)):
                    # We are looking for a user message followed by a model message
                    if chunks[i].get("role") == "user" and (i + 1) < len(chunks):
                        user_chunk = chunks[i]
                        # The next message might be a 'thought' chunk, we look for the next 'model' chunk
                        model_chunk = None
                        for j in range(i + 1, len(chunks)):
                            if chunks[j].get("role") == "model" and not chunks[j].get("isThought"):
                                model_chunk = chunks[j]
                                break
                        
                        if model_chunk:
                            user_text = user_chunk.get("text", "")
                            model_text = model_chunk.get("text", "")

                            # Create a unique hash for the pair to avoid duplicates
                            pair_content = user_text + model_text
                            content_hash = hashlib.md5(pair_content.encode('utf-8')).hexdigest()

                            if content_hash not in seen_hashes:
                                seen_hashes.add(content_hash)

                                # Save user part
                                user_filename = f"{chat_name}_{pair_counter:02d}_user.md"
                                user_filepath = os.path.join(output_dir, user_filename)
                                with open(user_filepath, 'w', encoding='utf-8') as out_f:
                                    out_f.write(user_text)
                                
                                # Save model part
                                model_filename = f"{chat_name}_{pair_counter:02d}_model.md"
                                model_filepath = os.path.join(output_dir, model_filename)
                                with open(model_filepath, 'w', encoding='utf-8') as out_f:
                                    out_f.write(model_text)

                                print(f"Processed pair {pair_counter} from {chat_name}")
                                pair_counter += 1

if __name__ == "__main__":
    INPUT_DIRECTORY = "original_chat_records"
    OUTPUT_DIRECTORY = "processed_chat_pairs"
    
    process_chat_files(INPUT_DIRECTORY, OUTPUT_DIRECTORY)
    print("\nChat processing complete.")
    print(f"Processed files are located in: {OUTPUT_DIRECTORY}") 