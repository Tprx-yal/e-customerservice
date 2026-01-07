from langchain_neo4j import Neo4jGraph
# from settings.lg_config import settings

# 本地Neo4j数据库配置
NEO4J_URL='bolt://localhost:7687'
NEO4J_USERNAME='neo4j'
NEO4J_PASSWORD='Tp1619902115'
NEO4J_DATABASE='neo4j'
def get_neo4j_graph() -> Neo4jGraph:
    """
    创建并返回一个Neo4jGraph实例，使用配置文件中的设置。
    
    Returns:
        Neo4jGraph: 配置好的Neo4j图数据库连接实例
    """
    # logger.info(f"initialize Neo4j connection: {settings.NEO4J_URL}")
    print("initialize Neo4j connection...")
    try:
        # 创建Neo4j图实例
        neo4j_graph = Neo4jGraph(
            url=NEO4J_URL,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            database=NEO4J_DATABASE
        )
        return neo4j_graph
    except Exception as e:
        raise