# Resultado do teste de fumaça

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
