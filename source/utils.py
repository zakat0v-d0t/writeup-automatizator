def detect_language(code: str) -> str:
    if not code:
        return "bash"
    
    if any(kw in code for kw in ["import ", "def ", "print(", "sys.", "requests.", "from "]):
        return "python"
    
    if any(kw in code for kw in ["#include", "int main", "printf(", "std::"]):
        return "c"
        
    code_lower = code.lower()
    if any(kw in code_lower for kw in ["select ", "union ", "insert ", "drop ", "where "]):
        return "sql"
        
    if any(kw in code for kw in ["console.log", "const ", "let ", "=>", "function("]):
        return "javascript"
        
    if "<?php" in code or "$_GET" in code or "$_POST" in code or "echo $" in code:
        return "php"
        
    if code.strip().startswith("{") and code.strip().endswith("}"):
        return "json"
        
    if any(kw in code_lower for kw in ["mov ", "push ", "pop ", "xor ", "eax,", "rax,", "jmp ", "ret"]):
        return "asm"
        
    return "bash"
