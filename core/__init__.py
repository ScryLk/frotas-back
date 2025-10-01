# Ativa PyMySQL como MySQLdb para o Django
try:
    import pymysql  # type: ignore
    pymysql.install_as_MySQLdb()
except Exception:
    # Permite que o projeto inicie mesmo se PyMySQL não estiver instalado no momento
    pass
