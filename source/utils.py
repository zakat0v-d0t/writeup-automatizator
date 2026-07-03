import re

def detect_language(code: str) -> str:
    if not code:
        return "bash"
    
    if re.search(r'\b(?:import|def|print|sys\.|requests\.|from)\b', code):
        return "python"
    
    if re.search(r'\b(?:#include|int main|printf|std::)\b', code):
        return "c"
        
    if re.search(r'\b(?:select|union|insert|drop|where)\b', code, re.IGNORECASE):
        return "sql"
        
    if re.search(r'\b(?:console\.log|const|let|function)\b|=>', code):
        return "javascript"
        
    if "<?php" in code or "$_GET" in code or "$_POST" in code or "echo $" in code:
        return "php"
        
    if code.strip().startswith("{") and code.strip().endswith("}"):
        return "json"
        
    if re.search(r'\b(?:mov|push|pop|xor|eax|rax|jmp|ret)\b', code, re.IGNORECASE):
        return "asm"
        
    return "bash"
