from groq import Groq

# Substitua pela sua chave do console.groq.com
chave_groq = "SUA_CHAVE_GROQ_AQUI"

try:
    client = Groq(api_key=chave_groq)
    completion = self.client.chat.completions.create(
        messages=[{"role": "user", "content": "Diga: Groq está ativa!"}],
        model="llama3-8b-8192",
    )
    print(f"✅ SUCESSO NA GROQ: {completion.choices[0].message.content}")
except Exception as e:
    print(f"❌ FALHA NA GROQ: {e}")