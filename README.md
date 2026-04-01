### 🛠️ APP\_SYNC\_FV: Pipeline de Integração AWS AppSync para SQL Server DW

#### 1\. 🎯 Visão Geral e Propósito

No atual ecossistema de engenharia de dados, a integração entre interfaces modernas de API, como o GraphQL, e ambientes de Data Warehouse (DW) relacionais tradicionais representa um desafio crítico de arquitetura. O projeto **APP\_SYNC\_FV** foi desenvolvido para preencher essa lacuna, atuando como um pipeline robusto que orquestra a extração de dados complexos — especificamente registros de visitas, serviços e seus respectivos anexos — originados no **AWS AppSync** para persistência estruturada no **Microsoft SQL Server**. O propósito central desta solução é automatizar o fluxo ETL (Extract, Transform, Load), garantindo que o DW atue como um espelho confiável das operações capturadas em campo. A estratégia foca na resiliência do pipeline e na integridade absoluta dos dados, assegurando que *stakeholders* técnicos e analistas de negócio tenham acesso a informações precisas para a tomada de decisão estratégica.

**Objetivos Principais:**

  * ⭐ **Extração Resiliente:** Mecanismos de paginação otimizados para grandes volumes de dados, mitigando *timeouts* e sobrecarga na API de origem.
  * ⭐ **Integridade Estrutural:** Gerenciamento autônomo de DDL para garantir que o esquema do banco de destino esteja sempre compatível com o domínio de dados.
  * ⭐ **Fidelidade de Dados:** Sincronização completa de registros, incluindo metadados de serviços e processamento de anexos.
  * ⭐ **Observabilidade de Produção:** Sistema de logs detalhado para auditoria e rápida resolução de incidentes em tempo de execução.

Esta base arquitetural permite uma operação estável, transformando dados brutos de API em ativos relacionais prontos para consumo analítico.

#### 2\. 🏗️ Arquitetura do Sistema

A escolha do padrão **Service-Repository** é o pilar desta arquitetura. Essa abordagem promove o desacoplamento entre a lógica de consumo da API GraphQL (domínio de extração) e a lógica de persistência no SQL Server (domínio de infraestrutura). Essa separação é vital para um arquiteto, pois permite que mudanças na estrutura da *query* GraphQL ou na versão do banco de dados sejam tratadas de forma isolada, garantindo escalabilidade e facilidade de manutenção a longo prazo.

``` mermaid
graph TD

    subgraph "Orquestração Principal"

        Main[main.py]

    end

    subgraph "Camada de Domínio (Business Logic)"

        Main --> FVS[FVService]

        Main --> FVM[FVSchemaManager]

    end

    subgraph "Camada de Infraestrutura (Connectors)"

        FVS --> GQLC[GraphQLClient]

        FVM --> SQLC[SQLServerConnector]

        FVR[FVRepositoryDW] --> SQLC

    end

    subgraph "Persistência e Destino"

        Main --> FVR

    end 
```

##### Padrões Arquiteturais Aplicados

  * 🧩 **Service-Repository:** O **FVService** encapsula as regras de negócio de extração e paginação, enquanto o **FVRepositoryDW** foca exclusivamente na eficiência operacional de escrita no SQL Server.
  * 🧩 **Injeção de Dependência:** Componentes de baixo nível, como o **GraphQLClient** e o **SQLServerConnector**, são injetados nas camadas de serviço, facilitando a testabilidade e a substituição de *drivers* de conexão sem afetar o *core* do sistema.

#### 3\. ➡️ Fluxo de Execução Passo a Passo

A consistência do pipeline é garantida por um fluxo linear rigorosamente orquestrado pelo `main.py`, assegurando que nenhuma carga ocorra sem a devida validação estrutural:

1.  1️⃣ **Inicialização e Observabilidade:** Configuração do *logger* para saída dupla (Console e arquivo em `./logs/`), estabelecendo a rastreabilidade desde o primeiro segundo de execução.
2.  2️⃣ **Carregamento de Configurações:** Leitura do arquivo `.env` e mapeamento para **Dataclasses** (*AppConfig* e *DBConfig*), garantindo tipagem forte e validação de credenciais em tempo de compilação/execução.
3.  3️⃣ **Setup de Conexões:** Instanciação dos túneis de comunicação via **GraphQLClient** e **SQLServerConnector**.
4.  4️⃣ **Validação de Schema (Idempotência):** O **FVSchemaManager** verifica a existência das tabelas no DW. Caso não existam, executa o DDL de criação, garantindo que o pipeline seja auto-recuperável em ambientes novos.
5.  5️⃣ **Extração (Extract):** O **FVService** realiza o consumo da API AWS AppSync. Utiliza-se paginação (parâmetros *skip* e *take*) para extrair registros completos, anexos e serviços em lotes controlados.
6.  6️⃣ **Carga (Load):** O **FVRepositoryDW** executa a persistência final, utilizando a lógica de carga total para garantir a sincronia.

#### 4\. 📂 Estrutura do Repositório

A organização modular do código reflete a separação de responsabilidades, facilitando a governança e o isolamento de componentes:

``` 
APP_SYNC_FV/
├── connectors/          # ⚙️ Clientes de baixo nível (HTTP GraphQL, SQL Connector)
├── services/            # 🧠 Lógica de extração, paginação e mapeamento de domínio
├── repository/          # 💾 Persistência (Insert) e gestão de Schema (DDL)
├── logs/                # 📝 Histórico de execução e auditoria
├── tests/               # 🧪 Suíte de testes unitários e de integração
├── .env                 # 🔑 Variáveis de ambiente e segredos (não versionado)
├── main.py              # 🚀 Orquestrador central do pipeline
└── requirements.txt     # 📦 Gerenciamento de dependências Python

```

#### 5\. ⚙️ Configuração e Variáveis de Ambiente (.env)

O sistema utiliza o `python-dotenv` para gerenciar a portabilidade e a segurança. As variáveis de ambiente permitem que o mesmo código opere em diferentes estágios (Dev, Homolog, Prod) sem alterações estruturais.

**Exemplo de Arquivo `.env`:**

``` 
# Configurações de API (AWS AppSync)
APPSYNC_ENDPOINT_URL=https://exemplo.appsync-api.amazonaws.com/graphql
APPSYNC_API_KEY=da2-xxxxxxxxxxxxxxxxxxxx
FV_BATCH_SIZE=500

# Configurações de Banco de Dados (SQL Server)
SQL_SERVER_HOST=dw-producao.database.windows.net
SQL_SERVER_DB=DW_AGRO
SQL_SERVER_USER=svc_pipeline
SQL_SERVER_PWD=******** 
```

##### Detalhamento das Configurações

| Variável               | Descrição Técnica                                                     |
| :--------------------: | :-------------------------------------------------------------------: |
| `APPSYNC_ENDPOINT_URL` | URL do *endpoint* GraphQL no AWS AppSync.                             |
| `APPSYNC_API_KEY`      | Chave de autorização para as *queries* de extração.                   |
| `FV_BATCH_SIZE`        | Quantidade de registros por página (*take*) para controle de memória. |
| `SQL_SERVER_HOST`      | *Hostname* ou endereço IP do servidor SQL Server.                     |
| `SQL_SERVER_DB`        | Nome do banco de dados de destino para a carga.                       |
| `SQL_SERVER_USER`      | Usuário com permissões de DDL e DML.                                  |
| `SQL_SERVER_PWD`       | Senha de autenticação do usuário de banco de dados.                   |

#### 6\. 🧠 Componentes Principais e Engenharia de Dados

A arquitetura foi fragmentada em classes com responsabilidades exclusivas para maximizar o controle granular sobre os dados:

  * **GraphQLClient:** Gerencia as requisições HTTP, tratando a estrutura de envelopes GraphQL, autenticação e possíveis retentativas de rede.
  * **SQLServerConnector:** Responsável pelo *pool* de conexões e pela transacionalidade básica com o Microsoft SQL Server.
  * **FVService:** Atua como o motor de extração. Implementa a lógica de **paginação** técnica, controlando os ponteiros *skip* e *take* com base no `FV_BATCH_SIZE`. Este componente é responsável por consolidar a tríade de dados: registros principais, anexos e serviços vinculados.
  * **FVRepositoryDW:** Implementa a fase de **Insert** dentro da estratégia de carga. Ele recebe os dados em memória e realiza a persistência otimizada, garantindo que os tipos de dados do Python sejam corretamente mapeados para o T-SQL.
  * **FVSchemaManager:** Garante a estabilidade do DW através da gestão de DDL, assegurando que o ambiente de destino esteja íntegro antes do início da carga de dados.

#### 7\. ⚖️ Decisões Técnicas e Trade-offs

Como arquitetura sênior, as escolhas de *design* priorizam a integridade e a simplicidade operacional sobre a complexidade de performance prematura.

**Estratégia de Full Load (Truncate + Insert):** O pipeline adota o modelo de carga total em cada execução.

  * **Racional Técnico:** O uso de `TRUNCATE` seguido de `INSERT` funciona como um mecanismo de salvaguarda contra "hard deletes" (exclusões definitivas) no sistema de origem. Como APIs GraphQL muitas vezes não expõem logs de deleção de forma trivial em *queries* padrão, a carga total garante que o DW seja um espelho fiel do estado atual do AppSync, eliminando registros "órfãos".
  * **Trade-off:** Esta abordagem aumenta o tráfego de rede e o tempo de processamento à medida que o volume cresce, podendo exigir uma transição para carga incremental no futuro.

**Uso de Dataclasses para Configurações:** A utilização de *Dataclasses* para *AppConfig* e *DBConfig* confere uma camada de validação que impede que erros de digitação em *strings* de configuração causem falhas silenciosas. Isso proporciona um código mais legível, tipado e fácil de debugar.

#### 8\. 👁️ Logs, Observabilidade e Testes

A visibilidade operacional é tratada como requisito funcional de primeira classe. O sistema implementa uma **estratégia de log de saída dupla**:

1.  💻 **Console (stdout):** Permite monitoramento em tempo real durante a execução por orquestradores (como Docker ou AWS ECS).
2.  📄 **Arquivo (`/logs/`):** Garante a persistência do histórico para análise forense de falhas e auditoria de volumetria de carga.

Quanto à qualidade, a modularidade facilitada pelo padrão *Service-Repository* permite a implementação de testes unitários isolados, onde o comportamento da API e do Banco de Dados pode ser simulado, garantindo que a lógica de transformação permaneça íntegra independentemente da infraestrutura.

#### 9\. 🗺️ Pontos de Atenção e Roadmap Futuro

Identificamos oportunidades de evolução para acompanhar o crescimento da demanda de dados.

**Pontos de Atenção:**

  * ⚠️ **Escalabilidade do Full Load:** O crescimento exponencial da base de dados pode tornar a janela de carga inviável para execuções muito frequentes.
  * ⚠️ **Limites da API:** O `FV_BATCH_SIZE` deve ser calibrado para respeitar os limites de memória da instância de execução e os *timeouts* do AppSync.

**Roadmap de Evolução:**

  * ✨ **Implementação de Carga Incremental:** Desenvolver lógica baseada em campos de *Last Modified Date* para reduzir o volume trafegado.
  * ✨ **Alertas e Notificações:** Integração com Slack ou e-mail para alertar falhas críticas no pipeline imediatamente.
  * ✨ **Paralelismo:** Explorar a extração paralela de páginas para reduzir o tempo total de execução (*Runtime*).

#### 10\. ✅ Conclusão

O **APP\_SYNC\_FV** é uma solução de engenharia de dados madura, projetada com foco em resiliência e manutenibilidade. Ao adotar padrões de *design* corporativos e uma estratégia de carga que prioriza a integridade dos dados (mitigando problemas de *hard deletes*), o pipeline oferece uma base sólida e confiável para sustentar as necessidades analíticas da organização, estando plenamente alinhado às melhores práticas de arquitetura de *software* modernas.
