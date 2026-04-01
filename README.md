flowchart LR
    %% NÍVEL ALTO: FLUXO GERAL
    subgraph AWS[☁️ AWS AppSync\n(GraphQL)]
        GQL[(GraphQL Endpoint\nFV)]
    end

    subgraph PY[🐍 APP_SYNC_FV (Python)]
        M[main.py\n(orquestrador)]

        subgraph CFG[Config]
            AC[AppConfig\n(config.py)]
            DBC[DBConfig\n(db_connection.py)]
        end

        subgraph API[Camada API FV]
            GClient[GraphQLClient\n(graphql_client.py)]
            FVServ[FVService\n(fv_service.py)]
        end

        subgraph DB[Camada DW]
            Conn[SQLServerConnector\n(db_connection.py)]
            Schema[FVSchemaManager\n(fv_schema.py)]
            Repo[FVRepositoryDW\n(fv_repository.py)]
        end
    end

    subgraph DW[🗄️ SQL Server\nDW_ALVORADA]
        T1[(FV_TIPO_SERVICO_VISITA)]
        T2[(FV_REGISTRO_VISITA)]
        T3[(FV_REGISTRO_VISITA_ANEXOS)]
        T4[(FV_REGISTRO_VISITA_SERVICOS)]
    end

    %% FLUXO
    M --> AC
    M --> DBC

    M --> GClient
    GClient --> GQL

    M --> FVServ
    FVServ --> GClient

    M --> Conn
    M --> Schema
    Schema --> Conn

    M --> Repo
    Repo --> Conn

    %% CARGA NO DW
    Repo --> T1
    Repo --> T2
    Repo --> T3
    Repo --> T4
