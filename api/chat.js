export default async function handler(req, res) {
  // Pega a pergunta que o seu site enviou
  const { prompt } = JSON.parse(req.body);

  // Faz a chamada para a OpenAI de forma segura
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}` // A chave fica guardada aqui!
    },
    body: JSON.stringify({
      model: "gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
    })
  });

  const data = await response.json();
  
  // Devolve apenas a resposta do GPT para o seu site
  res.status(200).json({ text: data.choices[0].message.content });
}
