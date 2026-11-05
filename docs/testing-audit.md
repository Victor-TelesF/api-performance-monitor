# Auditoria dos testes de erro

Execução de referência: 2026-11-05.

## O que foi encontrado

A suíte inicial executou **114 casos e ignorou 51 esboços**. Os esboços estavam
marcados com `skip`, portanto não eram contados como testes aprovados. Foram
substituídos por testes executáveis de listagem, estatísticas e erros de entrada.

Os testes existentes de status e mensagem tinham assertions úteis, mas vários
não verificavam os dados após uma rejeição. Além disso, o limite `150` do esboço
produzia a mesma contagem que o padrão `120` para `[100, 200]`: esse cenário não
conseguiria detectar um parâmetro ignorado. Os novos casos usam, entre outros,
o limite `200`, que altera o resultado e verifica a fronteira inclusiva.

Dois defeitos foram reproduzidos por testes falhando antes da correção:

- Um ID maior que o intervalo suportado chegava à consulta SQL e causava
  `OverflowError` no banco de teste. Os IDs HTTP agora devem estar entre `1` e
  `2147483647`, conforme as colunas `Integer` da migração PostgreSQL. IDs válidos
  e ausentes continuam devolvendo `404`; valores fora desse intervalo geram `422`.
- Uma exceção durante `figure.savefig()` deixava o buffer PNG aberto.
  A exportação agora fecha esse buffer e propaga a exceção original.

## Plano e verificações implementadas

| Área | Tipo de teste | Garantia verificada |
| --- | --- | --- |
| Domínio | Unitário com entradas concretas | Tipos inválidos, negativos, booleanos, `NaN`, infinitos, `Decimal`, overflow de conversão e preservação das medições. |
| Mapper | Unitário com schemas reais | Dataset ausente e validação antes da conversão para modelos persistíveis. |
| Handlers | Unitário e HTTP | Mensagem e distinção entre `404`, `409` e `422`; falhas internas continuam visíveis. |
| Datasets e medições | HTTP com SQLite isolado | Corpo ausente/malformado, IDs inválidos, latências inválidas, recursos ausentes, medição de outro dataset e conflito ao remover a última medição. |
| Estatísticas | HTTP com dados conhecidos | As 19 operações têm resultados independentes do código de cálculo, dataset ausente e IDs inválidos; parâmetros, limites, percentis e dispersão amostral são exercitados. |
| Visualizações | HTTP e exportação real | As cinco rotas geram PNGs decodificáveis; valores desenhados, gráfico solicitado, opções, erros e limpeza após falha são verificados. |
| Persistência após rejeição | Consulta direta às colunas | Os novos testes de erro de datasets e estatísticas comparam todas as linhas antes/depois e rejeitam alterações pendentes na sessão. |

O objetivo de cobertura é exercitar cada erro de negócio existente e cada
operação HTTP relevante, incluindo controles válidos que distinguem os ramos.
Não foi estabelecida uma meta artificial de porcentagem de linhas.

Os testes de estatística usam resultados conhecidos para `[100, 200]`, sem chamar
o próprio domínio para calcular o valor esperado. Moda e outliers também usam
um dataset que produz listas não vazias. As verificações dos gráficos inspecionam
os dados da figura real e depois executam a exportação real; não devolvem PNGs
falsos para simular sucesso.

`assert_http_error` consulta as colunas SQL em vez de confiar em objetos ORM
possivelmente já carregados. Verifica status, JSON, mensagem, linhas e alterações
pendentes. O SQLite habilita chaves estrangeiras. O `TestClient` mantém o padrão
de relançar exceções internas: um erro inesperado derruba o teste.

## Evidência por mutações

Foram introduzidas **20 regressões deliberadas** em uma cópia temporária dos
fontes e testes. Todas foram detectadas por casos falhando, sem erros de coleta.
As mutações cobriram:

- Aceitação indevida de booleanos, negativos, não finitos e percentil 101.
- Contagem com `>=` no lugar de `>` e variância amostral com uma medição.
- Parâmetros `sample`, `percent` e `threshold_ms` ignorados.
- Filtro de latência e ID da medição ignorados.
- Exclusão persistida da última medição antes de responder `409`.
- Coerção indevida de booleanos no corpo HTTP.
- Status incorretos para recursos ausentes e conflitos.
- Renderização do gráfico errado e tipo de conteúdo PNG incorreto.
- Buffer de exportação não fechado e figura não limpa após uma falha.
- Aceitação de ID zero.

Exemplo: a mutação que apaga a medição e ainda responde `409` falhou em
`test_last_measurement_conflict_preserves_the_persisted_row`. Um teste que
verificasse apenas o status e a mensagem aceitaria esse defeito.

Essa auditoria é uma amostra direcionada, não uma pontuação de mutação exaustiva
nem uma prova de ausência de defeitos. O executor exige uma suíte de controle
aprovada, sem skips, confere a importação da cópia temporária, valida a sintaxe
das mutações e diferencia falhas de testes de erros de coleta.

## Reproduzir

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/audit_error_mutations.py --report /tmp/api-error-mutations.json
docker compose config --quiet
```

Resultado desta execução: **498 casos aprovados, nenhum ignorado**, com um aviso
de depreciação do `BlockingPortal` em Starlette/AnyIO. A auditoria detectou
**20 de 20 mutações selecionadas**. O JSON gerado contém os casos que falharam
em cada mutação e a saída dos comandos.

## Limites e próximos testes

Os testes HTTP substituem a sessão por SQLite em memória. As variáveis de banco
da suíte usam credenciais de teste e um destino deliberadamente inválido, para
que uma dependência esquecida não conecte ao PostgreSQL do desenvolvedor.
A execução da suíte e das mutações não altera o banco em uso.

Ainda precisam de uma suíte de integração PostgreSQL descartável: migrações,
restrições específicas do banco, concorrência ao adicionar/remover medições,
falhas de conexão e falhas transacionais durante gravações. O SQLite e a amostra
de mutações não comprovam essas garantias. Também não foi feita uma auditoria
exaustiva de estabilidade numérica dos cálculos para valores próximos ao limite
de `float` nem uma medição de cobertura de linhas/ramos.
