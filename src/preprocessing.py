import pandas as pd
from pathlib import Path
from datetime import datetime


def load_and_preprocess_data(save_output=True):
    """
    Carrega e faz o pré-processamento básico dos dados de pedras.
    
    - Lê o arquivo Excel da pasta bases
    - Remove linhas onde a coluna PEDRA está vazia
    - Valida colunas obrigatórias
    - Converte colunas numéricas para tipo numérico
    - Salva o arquivo limpo em bases/treated com data de processamento
    
    Args:
        save_output (bool): Se True, salva o DataFrame processado
    
    Returns:
        pd.DataFrame: DataFrame limpo e processado
    """
    # Caminho para o arquivo Excel
    base_path = Path(__file__).parent / 'bases' / 'dados_pedras_baixo_erro.xlsx'
    
    # Lê o arquivo Excel
    df = pd.read_excel(base_path)
    
    # Colunas obrigatórias
    required_columns = ['PEDRA', 'IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
    
    # Valida se todas as colunas obrigatórias existem
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_columns}")
    
    # Remove linhas onde PEDRA está vazio
    df = df.dropna(subset=['PEDRA'])
    
    # Converte colunas numéricas para tipo numérico (todas exceto PEDRA)
    numeric_columns = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Trata valores vazios nas colunas numéricas
    # Se 2 ou mais colunas numéricas estiverem preenchidas, preencher as outras com 0
    # Caso contrário, remover a linha
    numeric_filled_count = df[numeric_columns].notna().sum(axis=1)
    valid_rows = numeric_filled_count >= 2
    
    # Remove linhas com menos de 2 colunas numéricas preenchidas
    df = df[valid_rows].copy()
    
    # Preenche valores vazios das colunas numéricas com 0
    df[numeric_columns] = df[numeric_columns].fillna(0)
    
    # Reset do índice após remoção de linhas
    df = df.reset_index(drop=True)
    
    # Adiciona student_id como entity key para o Feast Feature Store
    df.insert(0, 'student_id', range(len(df)))
    
    # Salva o arquivo processado em bases/treated
    if save_output:
        # Cria a pasta treated se não existir
        treated_path = Path(__file__).parent / 'bases' / 'treated'
        treated_path.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo com data de processamento
        today = datetime.now().strftime('%Y-%m-%d')
        output_file = treated_path / f'dados_pedras_processado_{today}.xlsx'
        
        # Salva o DataFrame limpo
        df.to_excel(output_file, index=False)
        print(f"\nArquivo salvo em: {output_file}")
    
    return df


if __name__ == '__main__':
    # Testa o processamento
    df = load_and_preprocess_data()
    
    print("=" * 50)
    print("Dados carregados e processados com sucesso!")
    print("=" * 50)
    print(f"\nShape do DataFrame: {df.shape}")
    print(f"Número de linhas: {df.shape[0]}")
    print(f"Número de colunas: {df.shape[1]}")
    print("\nColunas disponíveis:")
    print(df.columns.tolist())
    print("\nInformações do DataFrame:")
    print(df.info())
    print("\nPrimeiras 5 linhas:")
    print(df.head())
    print("\nEstatísticas descritivas:")
    print(df.describe())
