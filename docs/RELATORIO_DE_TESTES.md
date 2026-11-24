# Relatório de Testes — Camila Lee API (Django REST Framework)

**Disciplina:** Programação para Internet — TSI/IFB · **Projeto Final** (expansão da API do Projeto Integrador III)
**Gerado em:** 24/11/2026 18:23 · **Python** 3.13.18 · **Django** 5.2.19 · **pytest** 9.2.0

## 1. Objetivo e estratégia

Verificar, com evidências, os requisitos da rubrica: operações CRUD, validação e tratamento de erros,
autenticação e autorização, documentação, hospedagem/segurança e recursos adicionais (filtros, busca,
ordenação e paginação). Foram usadas três frentes complementares:

1. **Testes automatizados (pytest)** — rodam em banco isolado a cada execução (seção 2);
2. **Teste de fumaça HTTP (`scripts/smoke_test.py`)** — exercita a API por requisições reais, no servidor local
   em modo de produção e na **URL pública** (seção 3);
3. **Verificações de segurança e implantação** — `check --deploy` e conferências de configuração (seção 4).

Os testes manuais podem ser repetidos no **Swagger UI** (`/api/docs`) ou no Postman; as evidências em imagem
ficam listadas na seção 5.

## 2. Testes automatizados (pytest)

**Resultado da execução:** `140 passed in 1.64s`
(140 execuções de teste em 116 cenários; 0 falha(s)).
Comando: `python -m pytest` · Saída completa em `docs/evidencias/pytest.txt`.

| ID | Categoria | Cenário | Resultado esperado | Resultado obtido | Status |
|---|---|---|---|---|---|
| AUT-01 | CRUD | ADMIN lista usuários | HTTP 200 com todos os usuários (3) e sem campo de senha. | Conforme o esperado | ✅ Aprovado |
| AUT-02 | CRUD | ADMIN consulta um usuário | HTTP 200 (e 404 para id inexistente). | Conforme o esperado | ✅ Aprovado |
| AUT-03 | CRUD | ADMIN altera o perfil de um usuário | HTTP 200 e perfil persistido como ADMIN. | Conforme o esperado | ✅ Aprovado |
| AUT-04 | CRUD | ADMIN exclui um usuário | HTTP 204 e o usuário (e suas mensagens) somem do banco. | Conforme o esperado | ✅ Aprovado |
| AUT-05 | CRUD | ADMIN consulta o histórico de logins | HTTP 200 com 4 registros, do mais recente ao mais antigo. | Conforme o esperado | ✅ Aprovado |
| AUT-06 | CRUD | Consultar o próprio cadastro | HTTP 200 com os dados (sem senha). | Conforme o esperado | ✅ Aprovado |
| AUT-07 | CRUD | Atualizar o próprio cadastro (PUT e PATCH) | HTTP 200; e-mail e perfil não mudam mesmo se enviados. | Conforme o esperado | ✅ Aprovado |
| AUT-08 | CRUD | Excluir a própria conta | HTTP 204; usuário e mensagens removidos; histórico de logins mantido sem vínculo. | Conforme o esperado | ✅ Aprovado |
| AUT-09 | CRUD | Cadastrar usuário com dados válidos | HTTP 201, perfil USUARIO e nenhum campo de senha na resposta. | Conforme o esperado | ✅ Aprovado |
| AUT-10 | CRUD | Listar depoimentos sem estar autenticado | HTTP 200 com resultado paginado. | Conforme o esperado | ✅ Aprovado |
| AUT-11 | CRUD | Consultar depoimento sem estar autenticado | HTTP 200 com os dados do depoimento. | Conforme o esperado | ✅ Aprovado |
| AUT-12 | CRUD | ADMIN cria depoimento | HTTP 201 e registro gravado no banco. | Conforme o esperado | ✅ Aprovado |
| AUT-13 | CRUD | ADMIN atualiza depoimento (PUT e PATCH) | HTTP 200 e valores persistidos. | Conforme o esperado | ✅ Aprovado |
| AUT-14 | CRUD | ADMIN exclui depoimento | HTTP 204 e consulta posterior retorna 404. | Conforme o esperado | ✅ Aprovado |
| AUT-15 | CRUD | Criar mensagem autenticado | HTTP 201; remetente é o usuário logado e a mensagem fica gravada no banco. | Conforme o esperado | ✅ Aprovado |
| AUT-16 | CRUD | Listar mensagens | HTTP 200 paginado, contendo apenas as mensagens do próprio usuário. | Conforme o esperado | ✅ Aprovado |
| AUT-17 | CRUD | Consultar uma mensagem pelo id | HTTP 200 com os dados da mensagem. | Conforme o esperado | ✅ Aprovado |
| AUT-18 | CRUD | Atualizar mensagem (PUT) | HTTP 200 e novos valores persistidos no banco. | Conforme o esperado | ✅ Aprovado |
| AUT-19 | CRUD | Atualizar mensagem parcialmente (PATCH) | HTTP 200; muda só o campo enviado. | Conforme o esperado | ✅ Aprovado |
| AUT-20 | CRUD | Excluir mensagem | HTTP 204; consulta posterior retorna 404 e o registro some do banco. | Conforme o esperado | ✅ Aprovado |
| AUT-21 | Validação | ADMIN informa um perfil que não existe | HTTP 400 com erro em perfil. | Conforme o esperado | ✅ Aprovado |
| AUT-22 | Validação | ADMIN tenta alterar o e-mail de um usuário | HTTP 200, mas o e-mail permanece o mesmo (campo somente leitura). | Conforme o esperado | ✅ Aprovado |
| AUT-23 | Validação | ADMIN tenta rebaixar o próprio perfil | HTTP 400. | Conforme o esperado | ✅ Aprovado |
| AUT-24 | Validação | ADMIN tenta excluir a própria conta pelo endpoint administrativo | HTTP 400 e a conta continua existindo. | Conforme o esperado | ✅ Aprovado |
| AUT-25 | Validação | Parâmetro dias fora do intervalo ou não numérico | HTTP 400 com erro em dias. | Conforme o esperado | ✅ Aprovado |
| AUT-26 | Validação | Cadastrar e-mail já existente (inclusive com maiúsculas) | HTTP 409 com mensagem de conflito. | Conforme o esperado | ✅ Aprovado |
| AUT-27 | Validação | Login sem enviar e-mail e senha | HTTP 400 com erros por campo. | Conforme o esperado | ✅ Aprovado |
| AUT-28 | Validação | Logout com refresh inválido | HTTP 400 com erro no campo refresh. | Conforme o esperado | ✅ Aprovado |
| AUT-29 | Validação | Redefinir senha com código errado | HTTP 400 'Código inválido ou expirado.' | Conforme o esperado | ✅ Aprovado |
| AUT-30 | Validação | Redefinir senha com código expirado | HTTP 400. | Conforme o esperado | ✅ Aprovado |
| AUT-31 | Validação | Redefinir senha com senha fraca | HTTP 400 com erro em nova_senha. | Conforme o esperado | ✅ Aprovado |
| AUT-32 | Validação | Cadastro sem nenhum campo obrigatório | HTTP 400 com um erro para cada campo (nome, email, telefone, senha). | Conforme o esperado | ✅ Aprovado |
| AUT-33 | Validação | Mensagem sem serviço e sem texto | HTTP 400 com erros em servico e mensagem. | Conforme o esperado | ✅ Aprovado |
| AUT-34 | Validação | Depoimento sem campos obrigatórios | HTTP 400 com erros em nome_autor, profissao e texto. | Conforme o esperado | ✅ Aprovado |
| AUT-35 | Validação | Mensagem só com espaços em branco | HTTP 400 (texto vazio não é aceito). | Conforme o esperado | ✅ Aprovado |
| AUT-36 | Validação | Cadastro com tipo de dado incorreto (número, lista ou objeto em campo de texto) | HTTP 400 com erro no campo enviado. | Conforme o esperado (4 variações) | ✅ Aprovado |
| AUT-37 | Validação | Mensagem com tipo incorreto no texto (número, booleano, lista ou nulo) | HTTP 400 com erro no campo mensagem. | Conforme o esperado (4 variações) | ✅ Aprovado |
| AUT-38 | Validação | Cadastro com e-mail em formato inválido | HTTP 400 com erro em email. | Conforme o esperado (5 variações) | ✅ Aprovado |
| AUT-39 | Validação | Cadastro com telefone inválido | HTTP 400 com erro em telefone. | Conforme o esperado (5 variações) | ✅ Aprovado |
| AUT-40 | Validação | Telefones brasileiros em formatos comuns | HTTP 201. | Conforme o esperado (4 variações) | ✅ Aprovado |
| AUT-41 | Validação | Senha curta, só numérica ou muito comum | HTTP 400 com explicação da regra violada. | Conforme o esperado (4 variações) | ✅ Aprovado |
| AUT-42 | Validação | Nome com mais de 120 caracteres | HTTP 400 com erro em nome. | Conforme o esperado | ✅ Aprovado |
| AUT-43 | Validação | Serviço fora da enumeração (NOIVAS, AUDIOVISUAL, CORTE_CABELO, CARACTERIZACAO, OUTROS) | HTTP 400 listando os valores aceitos. | Conforme o esperado | ✅ Aprovado |
| AUT-44 | Validação | Mensagem com mais de 1000 caracteres | HTTP 400 com erro em mensagem. | Conforme o esperado | ✅ Aprovado |
| AUT-45 | Validação | Mensagem com exatamente 1000 caracteres | HTTP 201. | Conforme o esperado | ✅ Aprovado |
| AUT-46 | Validação | Depoimento com mais de 2000 caracteres | HTTP 400 com erro em texto. | Conforme o esperado | ✅ Aprovado |
| AUT-47 | Validação | Atualizar o próprio cadastro com telefone inválido | HTTP 400 com erro em telefone. | Conforme o esperado | ✅ Aprovado |
| AUT-48 | Validação | PUT (atualização completa) sem enviar todos os campos | HTTP 400 apontando o campo ausente. | Conforme o esperado | ✅ Aprovado |
| AUT-49 | Validação | Corpo da requisição com JSON malformado | HTTP 400 com mensagem clara. | Conforme o esperado | ✅ Aprovado |
| AUT-50 | Validação | Corpo JSON que é uma lista em vez de objeto | HTTP 400. | Conforme o esperado | ✅ Aprovado |
| AUT-51 | Validação | Envio como formulário (não JSON) | HTTP 415. | Conforme o esperado | ✅ Aprovado |
| AUT-52 | Validação | Consultar registro que não existe | HTTP 404 no formato padrão de erro. | Conforme o esperado | ✅ Aprovado |
| AUT-53 | Validação | Identificador que não é número | HTTP 404 (e não erro 500). | Conforme o esperado | ✅ Aprovado |
| AUT-54 | Validação | Consultar depoimento inexistente | HTTP 404. | Conforme o esperado | ✅ Aprovado |
| AUT-55 | Validação | Atualizar e excluir registro que não existe | HTTP 404 em ambos. | Conforme o esperado | ✅ Aprovado |
| AUT-56 | Validação | Endereço que não existe | HTTP 404 em JSON. | Conforme o esperado | ✅ Aprovado |
| AUT-57 | Validação | Método HTTP não suportado pelo endpoint | HTTP 405. | Conforme o esperado | ✅ Aprovado |
| AUT-58 | Validação | Filtro de data em formato inválido | HTTP 400 com erro em data_inicio. | Conforme o esperado | ✅ Aprovado |
| AUT-59 | Validação | Página fora do intervalo | HTTP 404. | Conforme o esperado | ✅ Aprovado |
| AUT-60 | Autenticação | Rotas administrativas sem token | HTTP 401. | Conforme o esperado (3 variações) | ✅ Aprovado |
| AUT-61 | Autenticação | Senha gravada apenas como hash PBKDF2 | valor no banco diferente da senha enviada e com prefixo pbkdf2_sha256. | Conforme o esperado | ✅ Aprovado |
| AUT-62 | Autenticação | Login com credenciais válidas | HTTP 200 com tokens access e refresh e dados do usuário. | Conforme o esperado | ✅ Aprovado |
| AUT-63 | Autenticação | Login com senha incorreta | HTTP 401 com mensagem genérica. | Conforme o esperado | ✅ Aprovado |
| AUT-64 | Autenticação | Login com e-mail que não existe | HTTP 401 com a MESMA mensagem da senha errada (não revela se a conta existe). | Conforme o esperado | ✅ Aprovado |
| AUT-65 | Autenticação | Login de conta desativada | HTTP 401. | Conforme o esperado | ✅ Aprovado |
| AUT-66 | Autenticação | Login enviado com um cabeçalho Authorization inválido | HTTP 200 (o login é público e ignora o cabeçalho). | Conforme o esperado | ✅ Aprovado |
| AUT-67 | Autenticação | Muitas tentativas de login seguidas (força bruta) | após 10 tentativas, HTTP 429 com cabeçalho Retry-After. | Conforme o esperado | ✅ Aprovado |
| AUT-68 | Autenticação | Cada tentativa de login é registrada no histórico | um registro SUCESSO e um FALHA, com IP, navegador e sistema do User-Agent. | Conforme o esperado | ✅ Aprovado |
| AUT-69 | Autenticação | Acessar rota protegida sem token | HTTP 401. | Conforme o esperado | ✅ Aprovado |
| AUT-70 | Autenticação | Acessar rota protegida com token inválido | HTTP 401. | Conforme o esperado | ✅ Aprovado |
| AUT-71 | Autenticação | Acessar rota protegida com token válido (obtido pelo login) | HTTP 200 com os dados do próprio usuário. | Conforme o esperado | ✅ Aprovado |
| AUT-72 | Autenticação | Token de acesso expirado | HTTP 401. | Conforme o esperado | ✅ Aprovado |
| AUT-73 | Autenticação | Renovar o token com refresh válido | HTTP 200 com novo par de tokens; reusar o refresh antigo retorna 401. | Conforme o esperado | ✅ Aprovado |
| AUT-74 | Autenticação | Renovar com refresh inválido | HTTP 401. | Conforme o esperado | ✅ Aprovado |
| AUT-75 | Autenticação | Logout com refresh válido | HTTP 204; depois disso o refresh não funciona mais (401). | Conforme o esperado | ✅ Aprovado |
| AUT-76 | Autenticação | Logout sem estar autenticado | HTTP 401. | Conforme o esperado | ✅ Aprovado |
| AUT-77 | Autenticação | Recuperar senha com código enviado por e-mail | e-mail enviado com código de 6 dígitos; nova senha funciona, a antiga não; o mesmo código não pode ser reutilizado. | Conforme o esperado | ✅ Aprovado |
| AUT-78 | Autenticação | Pedir código para e-mail inexistente | HTTP 200 com a mesma resposta de um e-mail existente e nenhum e-mail enviado. | Conforme o esperado | ✅ Aprovado |
| AUT-79 | Autenticação | Pedir um segundo código | o primeiro deixa de valer (HTTP 400) e o segundo funciona (HTTP 200). | Conforme o esperado | ✅ Aprovado |
| AUT-80 | Autenticação | Trocar a senha encerra as sessões abertas | refresh emitido antes da troca passa a retornar 401. | Conforme o esperado | ✅ Aprovado |
| AUT-81 | Autenticação | Criar depoimento sem token | HTTP 401. | Conforme o esperado | ✅ Aprovado |
| AUT-82 | Autenticação | Acessar mensagens sem token | HTTP 401 em listar, criar, consultar e excluir. | Conforme o esperado | ✅ Aprovado |
| AUT-83 | Autorização | Usuário comum tenta acessar rota administrativa | HTTP 403. | Conforme o esperado (3 variações) | ✅ Aprovado |
| AUT-84 | Autorização | ADMIN desativa uma conta | HTTP 200 e o usuário não consegue mais fazer login (401). | Conforme o esperado | ✅ Aprovado |
| AUT-85 | Autorização | Tentar criar registro de histórico pela API | HTTP 405 (o histórico só é gravado pelo login). | Conforme o esperado | ✅ Aprovado |
| AUT-86 | Autorização | Cliente tenta se cadastrar como ADMIN (escalada de privilégio) | HTTP 201, mas o perfil criado é USUARIO. | Conforme o esperado | ✅ Aprovado |
| AUT-87 | Autorização | Usuário comum (perfil USUARIO) tenta criar depoimento | HTTP 403. | Conforme o esperado | ✅ Aprovado |
| AUT-88 | Autorização | Usuário comum tenta alterar e excluir depoimento | HTTP 403 e o registro permanece. | Conforme o esperado | ✅ Aprovado |
| AUT-89 | Autorização | Enviar mensagem tentando se passar por outro usuário | HTTP 201, mas o remetente continua sendo o usuário autenticado. | Conforme o esperado | ✅ Aprovado |
| AUT-90 | Autorização | Usuário comum tenta consultar mensagem de outro usuário | HTTP 404 (não revela que o registro existe). | Conforme o esperado | ✅ Aprovado |
| AUT-91 | Autorização | Usuário comum tenta alterar e excluir mensagem de outro usuário | HTTP 404 e o registro permanece intacto. | Conforme o esperado | ✅ Aprovado |
| AUT-92 | Autorização | ADMIN lista mensagens | HTTP 200 com as mensagens de todos os usuários. | Conforme o esperado | ✅ Aprovado |
| AUT-93 | Autorização | ADMIN exclui mensagem de outro usuário | HTTP 204. | Conforme o esperado | ✅ Aprovado |
| AUT-94 | Hospedagem | Verificação de disponibilidade | HTTP 200 {"status": "ok"} sem autenticação. | Conforme o esperado | ✅ Aprovado |
| AUT-95 | Hospedagem | Documentação online (Swagger UI e ReDoc) | HTTP 200 em /api/docs e /api/redoc. | Conforme o esperado | ✅ Aprovado |
| AUT-96 | Hospedagem | Esquema OpenAPI publicado em /api/schema | HTTP 200, esquema de segurança Bearer JWT e todos os endpoints documentados. | Conforme o esperado | ✅ Aprovado |
| AUT-97 | Hospedagem | Documentação indica quais rotas exigem autenticação | /usuarios/me exige jwtAuth; /auth/login não exige. | Conforme o esperado | ✅ Aprovado |
| AUT-98 | Hospedagem | Cabeçalhos de segurança nas respostas | X-Content-Type-Options=nosniff e X-Frame-Options=DENY. | Conforme o esperado | ✅ Aprovado |
| AUT-99 | Hospedagem | Requisição HTTP quando o redirecionamento para HTTPS está ativo | HTTP 301 para o endereço https://. | Conforme o esperado | ✅ Aprovado |
| AUT-100 | Hospedagem | Requisição que chegou por HTTPS ao proxy (X-Forwarded-Proto: https) | HTTP 200 (sem laço de redirecionamento). | Conforme o esperado | ✅ Aprovado |
| AUT-101 | Hospedagem | Health check do provedor chega por HTTP interno | HTTP 200 mesmo com redirecionamento para HTTPS ativo (rota isenta). | Conforme o esperado | ✅ Aprovado |
| AUT-102 | Hospedagem | Erro inesperado no servidor | HTTP 500 com mensagem genérica, sem traceback nem texto da exceção. | Conforme o esperado | ✅ Aprovado |
| AUT-103 | Hospedagem | Painel do Django não fica no endereço previsível /admin/ | /admin/ retorna 404; o caminho configurado (ADMIN_URL) existe. | Conforme o esperado | ✅ Aprovado |
| AUT-104 | Recursos adicionais | ADMIN filtra por perfil e busca por nome | perfil=ADMIN retorna 1; search=João retorna 1. | Conforme o esperado | ✅ Aprovado |
| AUT-105 | Recursos adicionais | Histórico filtrado por status e buscado por navegador | status=FALHA retorna 1; search=Firefox retorna 1. | Conforme o esperado | ✅ Aprovado |
| AUT-106 | Recursos adicionais | Indicadores de acesso dos últimos 30 dias | 3 logins no total, 2 sucessos, 1 falha e último acesso preenchido. | Conforme o esperado | ✅ Aprovado |
| AUT-107 | Recursos adicionais | Filtrar depoimentos por profissão | somente os de 'noiva' (2), sem diferenciar maiúsculas. | Conforme o esperado | ✅ Aprovado |
| AUT-108 | Recursos adicionais | Buscar depoimentos por texto (search) | 'penteado' encontra 1 resultado. | Conforme o esperado | ✅ Aprovado |
| AUT-109 | Recursos adicionais | Ordenar depoimentos por nome | 'nome_autor' em ordem crescente e '-nome_autor' em decrescente. | Conforme o esperado | ✅ Aprovado |
| AUT-110 | Recursos adicionais | Paginar depoimentos com page_size=2 | 2 itens na página 1, 1 item na página 2 e count=3. | Conforme o esperado | ✅ Aprovado |
| AUT-111 | Recursos adicionais | page_size acima do máximo (100) | a API limita o tamanho da página a 100 (HTTP 200). | Conforme o esperado | ✅ Aprovado |
| AUT-112 | Recursos adicionais | Filtrar mensagens por serviço | somente as mensagens do serviço NOIVAS (2). | Conforme o esperado | ✅ Aprovado |
| AUT-113 | Recursos adicionais | Filtrar mensagens por período (data_inicio) | apenas as enviadas nos últimos 2 dias (2). | Conforme o esperado | ✅ Aprovado |
| AUT-114 | Recursos adicionais | Buscar mensagens por texto (search) | apenas as que contêm 'maquiagem' (2). | Conforme o esperado | ✅ Aprovado |
| AUT-115 | Recursos adicionais | Ordenar mensagens por data (ordering) | crescente com 'enviado_em' e decrescente com '-enviado_em'. | Conforme o esperado | ✅ Aprovado |
| AUT-116 | Recursos adicionais | Paginar mensagens (page e page_size) | 2 itens por página, count=4 e links next/previous corretos. | Conforme o esperado | ✅ Aprovado |

Os cenários mínimos da rubrica estão cobertos: CRUD completo (criar, listar, consultar, atualizar e excluir),
mais de três cenários de dados inválidos, acesso sem autenticação / com credenciais inválidas / com credenciais
válidas, operação não autorizada (usuário comum x ADMIN) e recursos adicionais (filtros, busca, ordenação, paginação).

## 3. Teste de fumaça HTTP (esperado x obtido por requisição)

### 3.1 Servidor local em modo de produção (gunicorn, DEBUG=False)

#### Resultado do teste de fumaça

- **URL testada:** http://127.0.0.1:8766
- **Data/hora:** 24/11/2026 18:21:48
- **Resultado:** 40 de 40 cenários conforme o esperado

| ID | Categoria | Cenário | Requisição | Esperado | Obtido | Tempo | Status |
|---|---|---|---|---|---|---|---|
| HT-01 | Hospedagem | Health check da API | `GET /api/saude` | HTTP 200 | HTTP 200 | 164 ms | ✅ Aprovado |
| HT-02 | Hospedagem | Swagger UI disponível | `GET /api/docs` | HTTP 200 | HTTP 200 | 165 ms | ✅ Aprovado |
| HT-03 | Hospedagem | Esquema OpenAPI disponível | `GET /api/schema` | HTTP 200 | HTTP 200 | 188 ms | ✅ Aprovado |
| HT-04 | Hospedagem | ReDoc disponível | `GET /api/redoc` | HTTP 200 | HTTP 200 | 3 ms | ✅ Aprovado |
| HT-05 | Autenticação | Rota protegida sem token | `GET /api/usuarios/me` | HTTP 401 | HTTP 401 | 2 ms | ✅ Aprovado |
| HT-06 | Autenticação | Cadastro de usuário válido | `POST /api/auth/cadastro` | HTTP 201 | HTTP 201 | 184 ms | ✅ Aprovado |
| HT-07 | Validação | Cadastro com e-mail já existente | `POST /api/auth/cadastro` | HTTP 409 | HTTP 409 | 4 ms | ✅ Aprovado |
| HT-08 | Autenticação | Login com senha incorreta | `POST /api/auth/login` | HTTP 401 | HTTP 401 | 159 ms | ✅ Aprovado |
| HT-09 | Autenticação | Login com credenciais válidas | `POST /api/auth/login` | HTTP 200 | HTTP 200 | 189 ms | ✅ Aprovado |
| HT-10 | Autenticação | Rota protegida com token válido | `GET /api/usuarios/me` | HTTP 200 | HTTP 200 | 12 ms | ✅ Aprovado |
| HT-11 | Autenticação | Rota protegida com token inválido | `GET /api/usuarios/me` | HTTP 401 | HTTP 401 | 2 ms | ✅ Aprovado |
| HT-12 | Validação | Cadastro sem campos obrigatórios | `POST /api/auth/cadastro` | HTTP 400 | HTTP 400 | 2 ms | ✅ Aprovado |
| HT-13 | Validação | Cadastro com e-mail inválido | `POST /api/auth/cadastro` | HTTP 400 | HTTP 400 | 2 ms | ✅ Aprovado |
| HT-14 | Validação | Cadastro com tipo incorreto (nome numérico) | `POST /api/auth/cadastro` | HTTP 400 | HTTP 400 | 2 ms | ✅ Aprovado |
| HT-15 | Validação | Mensagem com serviço inválido | `POST /api/mensagens` | HTTP 400 | HTTP 400 | 3 ms | ✅ Aprovado |
| HT-16 | Validação | Mensagem sem texto | `POST /api/mensagens` | HTTP 400 | HTTP 400 | 3 ms | ✅ Aprovado |
| HT-17 | Validação | Registro inexistente | `GET /api/mensagens/99999999` | HTTP 404 | HTTP 404 | 5 ms | ✅ Aprovado |
| HT-18 | CRUD | Criar mensagem | `POST /api/mensagens` | HTTP 201 | HTTP 201 | 6 ms | ✅ Aprovado |
| HT-19 | CRUD | Listar mensagens | `GET /api/mensagens` | HTTP 200 | HTTP 200 | 6 ms | ✅ Aprovado |
| HT-20 | CRUD | Consultar mensagem | `GET /api/mensagens/1` | HTTP 200 | HTTP 200 | 5 ms | ✅ Aprovado |
| HT-21 | CRUD | Atualizar mensagem (PUT) | `PUT /api/mensagens/1` | HTTP 200 | HTTP 200 | 8 ms | ✅ Aprovado |
| HT-22 | CRUD | Atualizar mensagem (PATCH) | `PATCH /api/mensagens/1` | HTTP 200 | HTTP 200 | 10 ms | ✅ Aprovado |
| HT-23 | Recursos adicionais | Filtrar mensagens por serviço | `GET /api/mensagens?servico=OUTROS` | HTTP 200 | HTTP 200 | 4 ms | ✅ Aprovado |
| HT-24 | Recursos adicionais | Buscar e ordenar mensagens | `GET /api/mensagens?search=atualizado&ordering=-enviado_em` | HTTP 200 | HTTP 200 | 7 ms | ✅ Aprovado |
| HT-25 | CRUD | Excluir mensagem | `DELETE /api/mensagens/1` | HTTP 204 | HTTP 204 | 6 ms | ✅ Aprovado |
| HT-26 | CRUD | Consultar mensagem excluída | `GET /api/mensagens/1` | HTTP 404 | HTTP 404 | 4 ms | ✅ Aprovado |
| HT-27 | Autorização | Usuário comum acessa rota de ADMIN | `GET /api/admin/usuarios` | HTTP 403 | HTTP 403 | 2 ms | ✅ Aprovado |
| HT-28 | Autorização | Usuário comum cria depoimento | `POST /api/depoimentos` | HTTP 403 | HTTP 403 | 2 ms | ✅ Aprovado |
| HT-29 | CRUD | Listar depoimentos (público) | `GET /api/depoimentos` | HTTP 200 | HTTP 200 | 2 ms | ✅ Aprovado |
| HT-30 | Recursos adicionais | Paginação de depoimentos | `GET /api/depoimentos?page=1&page_size=2` | HTTP 200 | HTTP 200 | 2 ms | ✅ Aprovado |
| HT-31 | Recursos adicionais | Busca e ordenação de depoimentos | `GET /api/depoimentos?search=noiva&ordering=-criado_em` | HTTP 200 | HTTP 200 | 3 ms | ✅ Aprovado |
| HT-32 | Autenticação | Login do ADMIN | `POST /api/auth/login` | HTTP 200 | HTTP 200 | 171 ms | ✅ Aprovado |
| HT-33 | CRUD | ADMIN cria depoimento | `POST /api/depoimentos` | HTTP 201 | HTTP 201 | 7 ms | ✅ Aprovado |
| HT-34 | CRUD | Consultar depoimento (público) | `GET /api/depoimentos/1` | HTTP 200 | HTTP 200 | 4 ms | ✅ Aprovado |
| HT-35 | CRUD | ADMIN atualiza depoimento | `PATCH /api/depoimentos/1` | HTTP 200 | HTTP 200 | 8 ms | ✅ Aprovado |
| HT-36 | CRUD | ADMIN exclui depoimento | `DELETE /api/depoimentos/1` | HTTP 204 | HTTP 204 | 7 ms | ✅ Aprovado |
| HT-37 | Autorização | ADMIN lista usuários | `GET /api/admin/usuarios?page_size=5` | HTTP 200 | HTTP 200 | 4 ms | ✅ Aprovado |
| HT-38 | Autorização | ADMIN consulta histórico de logins | `GET /api/admin/logins?status=SUCESSO` | HTTP 200 | HTTP 200 | 6 ms | ✅ Aprovado |
| HT-39 | Autorização | ADMIN consulta indicadores de acesso | `GET /api/admin/logins/resumo` | HTTP 200 | HTTP 200 | 3 ms | ✅ Aprovado |
| HT-40 | CRUD | Excluir a própria conta (limpeza) | `DELETE /api/usuarios/me` | HTTP 204 | HTTP 204 | 7 ms | ✅ Aprovado |

### 3.2 URL pública (ambiente de produção)

> **PENDENTE.** Depois de publicar a API, execute `python scripts/smoke_test.py https://SUA-API.onrender.com --admin-email EMAIL --admin-senha SENHA --saida docs/evidencias/smoke_publico.md` e gere este relatório novamente.

## 4. Hospedagem e segurança

| Item da rubrica | Como foi atendido | Como foi verificado |
|---|---|---|
| `DEBUG = False` | Padrão do projeto é `False`; só liga com `DEBUG=True` no `.env` local. `render.yaml` fixa `False`. | Teste `test_erro_interno_nao_vaza_detalhes` (erro 500 sem traceback). |
| `ALLOWED_HOSTS` | Lido de variável de ambiente; no Render inclui `RENDER_EXTERNAL_HOSTNAME`. Vazio em produção = recusa tudo. | Host não autorizado recebe HTTP 400 (verificado manualmente). |
| `SECRET_KEY` e credenciais | Somente variáveis de ambiente; a aplicação **se recusa a iniciar** sem `SECRET_KEY` quando `DEBUG=False`. `.env` está no `.gitignore`. | Execução sem a variável: `ImproperlyConfigured` (verificado manualmente). |
| HTTPS | `SECURE_SSL_REDIRECT`, HSTS de 1 ano, cookies `Secure`, `SECURE_PROXY_SSL_HEADER` (proxy do provedor). | Testes `test_redireciona_http_para_https`, `test_https_atras_do_proxy_nao_redireciona`. |
| Exposição do banco | `DATABASE_URL` interna (não pública) em variável de ambiente; erros 500 genéricos; painel Django em caminho configurável (`ADMIN_URL`). | Testes `test_admin_do_django_fora_do_caminho_padrao`, `test_erro_interno_nao_vaza_detalhes`. |
| Senhas | Hash PBKDF2 + validadores de senha do Django; respostas nunca trazem a senha. | Teste `test_senha_armazenada_com_hash`. |
| Força bruta | Limite por IP em login (10/min), cadastro, recuperação e redefinição de senha. | Teste `test_login_limite_de_tentativas` (HTTP 429). |
| Documentação online | Swagger UI, ReDoc e esquema OpenAPI no mesmo servidor, com arquivos estáticos locais (sem CDN). | Testes `test_swagger_ui_e_redoc_disponiveis`, `test_esquema_openapi_completo`. |

### 4.1 `python manage.py check --deploy`

```
$ DEBUG=False SECRET_KEY=<chave forte> ALLOWED_HOSTS=minha-api.onrender.com python manage.py check --deploy
System check identified some issues:

WARNINGS:
?: (security.W021) You have not set the SECURE_HSTS_PRELOAD setting to True. Without this, your site cannot be submitted to the browser preload list.

System check identified 1 issue (0 silenced).
```

**Análise do aviso `security.W021` (HSTS preload):** mantido de propósito. O *preload* inclui o domínio
numa lista embutida nos navegadores e é difícil de desfazer; só deve ser ativado para um domínio próprio e
definitivo (variável `SECURE_HSTS_PRELOAD=True`). Em `*.onrender.com` o domínio pertence ao provedor, portanto
o aviso é conhecido e aceito. Todos os demais avisos (SSL redirect, cookies seguros, HSTS, `DEBUG`,
`SECRET_KEY`, `ALLOWED_HOSTS`) estão resolvidos.

## 5. Evidências a anexar (capturas de tela)

- [ ] Swagger UI na URL pública (`/api/docs`) com a lista completa de endpoints.
- [ ] Botão **Authorize** preenchido e uma rota protegida respondendo 200.
- [ ] Rota protegida sem token respondendo **401** e rota de ADMIN com usuário comum respondendo **403**.
- [ ] Cadastro (**201**), login (**200**) e login inválido (**401**) no Swagger ou Postman.
- [ ] CRUD de mensagens: criar (**201**), listar, consultar, atualizar e excluir (**204**).
- [ ] Erro de validação (**400**) com o JSON de `detalhes`.
- [ ] Cadeado/HTTPS no navegador e HTTP redirecionando para HTTPS.
- [ ] Painel do provedor mostrando as variáveis de ambiente (**sem exibir os valores secretos**).
- [ ] Execução do `check --deploy` no terminal.

## 6. Conclusão

Todos os cenários automatizados foram aprovados.
O teste de fumaça local confirma o funcionamento da API em modo de produção; a seção 3.2 registra a execução
contra a URL pública após a implantação.
