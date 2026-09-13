# Avaliação da Unidade I

Construir um agente capaz de resolver uma **tarefa verificável**, isto é, uma tarefa para a qual seja possível determinar objetivamente se a resposta produzida está correta ou incorreta. O tema é livre e a implementação deve utilizar o `agentkit`.

O trabalho será realizado em dupla.

## O agente

O agente deve atender aos seguintes requisitos:

1. Possuir pelo menos **três ferramentas desenvolvidas pela dupla**, utilizando `@tool`.
2. Resolver uma tarefa que envolva **múltiplas etapas**, de modo que pelo menos alguns casos exijam mais de uma ação ou chamada de ferramenta.
3. O modelo deve **decidir dinamicamente quais ferramentas utilizar, em que ordem e quando encerrar a execução**.
4. O **prompt e o contexto do agente** devem ser projetados pela dupla de acordo com a tarefa escolhida.
5. Implementar pelo menos **dois** dos seguintes mecanismos: saída estruturada, memória ou estado, planejamento e reflexão.

Os mecanismos escolhidos devem ter uma função real na solução e não devem ser adicionados apenas para cumprir o requisito.

O modelo fica a critério da dupla, podendo ser local, com `LLM`, ou acessado por API, com `LLMAPI`. No caso de API, a chave deve ser lida de uma variável de ambiente e não pode aparecer no notebook. Não é permitido utilizar LangChain ou outros frameworks de agentes.

## Entregável

A entrega consiste em um único notebook, que deve executar do início ao fim sem intervenção manual. A primeira célula deve conter o **título do trabalho e o nome dos dois participantes**.

O notebook deve incluir a implementação completa do agente e **dez casos de teste**. Os testes devem cobrir situações variadas da tarefa e pelo menos **três devem ser suficientemente desafiadores para explorar os limites do agente**. Pelo menos alguns casos devem exigir múltiplas etapas e o uso de mais de uma ferramenta.

Para cada teste, apresente a **entrada, o resultado esperado, o resultado obtido e se o teste foi aprovado ou não**. Ao final, informe a taxa de acerto e faça uma breve análise dos principais erros observados.

Também deve conter um breve relatório em células de Markdown no próprio notebook explicando o que o agente faz, por que a tarefa é verificável e as principais decisões de projeto.