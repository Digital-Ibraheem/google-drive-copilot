import re

def chunk_text(text, source, target_chunk_size=500):
    """
    Split text into chunks of approximately target_chunk_size words.
    Attempts to break at newlines and sentence boundaries when possible.
    
    Args:
        text (str): The text to be chunked
        source (str): Source identifier (file_id or title)
        target_chunk_size (int): Target size of each chunk in words
        
    Returns:
        list: List of dictionaries with format {"text": chunk_text, "source": source}
    """
    # Handle empty or None text
    if not text:
        return []
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for paragraph in paragraphs:
        # Skip empty paragraphs
        if not paragraph.strip():
            continue
            
        # If adding this paragraph would exceed our target size and we already have content,
        # finalize the current chunk and start a new one
        paragraph_word_count = len(paragraph.split())
        
        if current_word_count + paragraph_word_count > target_chunk_size and current_chunk:
            chunks.append({
                "text": '\n\n'.join(current_chunk),
                "source": source
            })
            current_chunk = []
            current_word_count = 0
        
        # If paragraph is small enough, add it whole
        if paragraph_word_count <= target_chunk_size:
            current_chunk.append(paragraph)
            current_word_count += paragraph_word_count
        else:
            # For large paragraphs, we need to split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                sentence_word_count = len(sentence.split())
                
                if current_word_count + sentence_word_count > target_chunk_size and current_chunk:
                    chunks.append({
                        "text": '\n\n'.join(current_chunk),
                        "source": source
                    })
                    current_chunk = []
                    current_word_count = 0
                
                current_chunk.append(sentence)
                current_word_count += sentence_word_count
                
                # If we've accumulated enough for a chunk, finalize it
                if current_word_count >= target_chunk_size:
                    chunks.append({
                        "text": '\n\n'.join(current_chunk),
                        "source": source
                    })
                    current_chunk = []
                    current_word_count = 0
    
    # Add any remaining text as the last chunk
    if current_chunk:
        chunks.append({
            "text": '\n\n'.join(current_chunk),
            "source": source
        })
    
    return chunks
