"""
Script para realizar predições usando o modelo XGBoost treinado.

Este script carrega um arquivo Excel com dados de alunos e gera classificações
(pedras) com base nos índices de desempenho.

Uso:
    python src/predict.py --input dados.xlsx --output predictions.csv
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from typing import Tuple, List, Dict


# Definir colunas esperadas (7 features de entrada)
REQUIRED_FEATURES = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']

# Classes de pedras esperadas
STONE_CLASSES = [
    'Ametista', 'Esmeralda', 'Onix', 'Quartzo', 
    'Rubi', 'Safira', 'Topazio', 'Turmalina'
]


def load_model_artifacts(models_path: str = 'app/modelo') -> Tuple:
    """
    Carrega os artefatos do modelo treinado.
    
    Args:
        models_path: Caminho para o diretório contendo os artefatos do modelo
        
    Returns:
        Tupla (model, label_encoder, feature_names)
        
    Raises:
        FileNotFoundError: Se os arquivos do modelo não forem encontrados
    """
    models_dir = Path(models_path)
    
    if not models_dir.exists():
        raise FileNotFoundError(
            f"Diretório de modelos não encontrado: {models_dir.absolute()}"
        )
    
    # Procurar arquivos do modelo (podem ter data no nome)
    model_files = list(models_dir.glob('xgboost_pedra_classifier_*.joblib'))
    encoder_files = list(models_dir.glob('label_encoder_*.pkl'))
    feature_files = list(models_dir.glob('feature_names_*.pkl'))
    
    if not model_files:
        raise FileNotFoundError(
            f"Modelo não encontrado em {models_dir.absolute()}. "
            "Procurando por: xgboost_pedra_classifier_*.joblib"
        )
    
    if not encoder_files:
        raise FileNotFoundError(
            f"Label encoder não encontrado em {models_dir.absolute()}. "
            "Procurando por: label_encoder_*.pkl"
        )
    
    if not feature_files:
        raise FileNotFoundError(
            f"Feature names não encontrado em {models_dir.absolute()}. "
            "Procurando por: feature_names_*.pkl"
        )
    
    # Usar o arquivo mais recente se houver múltiplos
    model_file = sorted(model_files)[-1]
    encoder_file = sorted(encoder_files)[-1]
    feature_file = sorted(feature_files)[-1]
    
    print(f"📦 Carregando modelo: {model_file.name}")
    print(f"📦 Carregando encoder: {encoder_file.name}")
    print(f"📦 Carregando features: {feature_file.name}")
    
    try:
        model = joblib.load(model_file)
        label_encoder = joblib.load(encoder_file)
        feature_names = joblib.load(feature_file)
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar artefatos do modelo: {str(e)}")
    
    return model, label_encoder, feature_names


def validate_and_preprocess(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Valida e preprocessa os dados de entrada.
    
    Aplica as mesmas transformações usadas durante o treinamento:
    - Verifica presença das colunas necessárias
    - Converte para numérico
    - Preenche valores faltantes com 0 (se a linha tiver >= 2 features válidas)
    - Rejeita linhas com menos de 2 features válidas
    
    Args:
        df: DataFrame com os dados de entrada
        
    Returns:
        Tupla (DataFrame processado, lista de avisos)
        
    Raises:
        ValueError: Se colunas obrigatórias estiverem ausentes
    """
    warnings = []
    df_copy = df.copy()
    
    # Verificar colunas obrigatórias
    missing_cols = [col for col in REQUIRED_FEATURES if col not in df_copy.columns]
    if missing_cols:
        raise ValueError(
            f"Colunas obrigatórias ausentes no arquivo: {', '.join(missing_cols)}\n"
            f"Colunas esperadas: {', '.join(REQUIRED_FEATURES)}"
        )
    
    # Adicionar índice original para rastreamento
    df_copy['_original_index'] = range(len(df_copy))
    
    # Converter para numérico
    for col in REQUIRED_FEATURES:
        original_type = df_copy[col].dtype
        df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
        
        # Rastrear conversões que geraram NaN
        na_count = df_copy[col].isna().sum()
        if na_count > 0:
            warnings.append(
                f"⚠️  Coluna '{col}': {na_count} valor(es) inválido(s) "
                f"convertido(s) para NaN (tipo original: {original_type})"
            )
    
    # Contar quantas features válidas cada linha tem
    numeric_filled_count = df_copy[REQUIRED_FEATURES].notna().sum(axis=1)
    
    # Identificar linhas a serem rejeitadas (< 2 features válidas)
    valid_rows = numeric_filled_count >= 2
    rejected_count = (~valid_rows).sum()
    
    if rejected_count > 0:
        rejected_indices = df_copy.loc[~valid_rows, '_original_index'].tolist()
        warnings.append(
            f"❌ {rejected_count} linha(s) rejeitada(s) por ter menos de 2 "
            f"features válidas (índices: {rejected_indices})"
        )
    
    # Filtrar linhas válidas
    df_processed = df_copy[valid_rows].copy()
    
    if len(df_processed) == 0:
        raise ValueError(
            "Nenhuma linha válida encontrada após validação. "
            "Todas as linhas têm menos de 2 features válidas."
        )
    
    # Identificar e preencher valores faltantes com 0
    for col in REQUIRED_FEATURES:
        na_mask = df_processed[col].isna()
        na_count = na_mask.sum()
        if na_count > 0:
            affected_indices = df_processed.loc[na_mask, '_original_index'].tolist()
            warnings.append(
                f"🔧 Coluna '{col}': {na_count} valor(es) faltante(s) "
                f"preenchido(s) com 0 (índices: {affected_indices})"
            )
            df_processed[col] = df_processed[col].fillna(0)
    
    # Remover coluna auxiliar
    df_processed = df_processed.drop(columns=['_original_index'])
    
    return df_processed, warnings


def predict_with_probabilities(
    model, 
    label_encoder, 
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Realiza predições com probabilidades para cada classe.
    
    Args:
        model: Modelo XGBoost treinado
        label_encoder: LabelEncoder para decodificar classes
        df: DataFrame com features preprocessadas
        
    Returns:
        DataFrame com colunas:
        - PEDRA_PREDITA: Classe predita (nome da pedra)
        - PROB_[classe]: Probabilidade para cada uma das 8 classes
        - CONFIANCA: Probabilidade máxima (confiança da predição)
    """
    # Garantir ordem correta das features
    X = df[REQUIRED_FEATURES].values
    
    # Fazer predições
    y_pred_encoded = model.predict(X)
    y_pred_proba = model.predict_proba(X)
    
    # Decodificar classes
    y_pred = label_encoder.inverse_transform(y_pred_encoded)
    
    # Criar DataFrame de resultados
    results = pd.DataFrame()
    results['PEDRA_PREDITA'] = y_pred
    
    # Adicionar probabilidades de cada classe
    class_names = label_encoder.classes_
    for i, class_name in enumerate(class_names):
        results[f'PROB_{class_name}'] = y_pred_proba[:, i]
    
    # Adicionar confiança (probabilidade máxima)
    results['CONFIANCA'] = y_pred_proba.max(axis=1)
    
    return results


def main():
    """Função principal que orquestra o pipeline de predição."""
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(
        description='Realizar predições de classificação de pedras usando modelo XGBoost',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python src/predict.py --input dados.xlsx
  python src/predict.py --input dados.xlsx --output resultados.csv
  python src/predict.py --input src/bases/dados_pedras_baixo_erro.xlsx --output predictions.csv

O arquivo de entrada deve conter as seguintes colunas:
  IPV, IPS, IAN, IEG, INDE, IAA, IDA
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Caminho para o arquivo Excel de entrada (.xlsx ou .xls)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='predictions.csv',
        help='Caminho para o arquivo CSV de saída (padrão: predictions.csv)'
    )
    
    parser.add_argument(
        '--models-path',
        type=str,
        default='app/modelo',
        help='Caminho para o diretório com os artefatos do modelo (padrão: app/modelo)'
    )
    
    args = parser.parse_args()
    
    # Validar arquivo de entrada
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Erro: Arquivo não encontrado: {input_path.absolute()}")
        sys.exit(1)
    
    if input_path.suffix.lower() not in ['.xlsx', '.xls']:
        print(f"❌ Erro: Formato de arquivo inválido: {input_path.suffix}")
        print("   Formatos aceitos: .xlsx, .xls")
        sys.exit(1)
    
    print("=" * 70)
    print("🔮 SISTEMA DE PREDIÇÃO DE CLASSIFICAÇÃO DE PEDRAS")
    print("=" * 70)
    print()
    
    try:
        # 1. Carregar dados
        print(f"📂 Carregando dados de: {input_path.name}")
        df_input = pd.read_excel(input_path)
        print(f"   ✓ {len(df_input)} linha(s) carregada(s)")
        print()
        
        # 2. Carregar modelo
        print("📦 Carregando artefatos do modelo...")
        model, label_encoder, feature_names = load_model_artifacts(args.models_path)
        print(f"   ✓ Modelo carregado com sucesso")
        print(f"   ✓ Classes disponíveis: {', '.join(label_encoder.classes_)}")
        print()
        
        # 3. Validar e preprocessar
        print("🔍 Validando e preprocessando dados...")
        df_processed, warnings = validate_and_preprocess(df_input)
        print(f"   ✓ {len(df_processed)} linha(s) válida(s) após preprocessamento")
        
        if warnings:
            print()
            print("⚠️  AVISOS:")
            for warning in warnings:
                print(f"   {warning}")
        print()
        
        # 4. Fazer predições
        print("🤖 Gerando predições...")
        predictions = predict_with_probabilities(model, label_encoder, df_processed)
        print(f"   ✓ Predições geradas com sucesso")
        print()
        
        # 5. Combinar dados originais com predições
        # Usar apenas as linhas que foram processadas
        df_output = pd.concat([
            df_processed.reset_index(drop=True),
            predictions.reset_index(drop=True)
        ], axis=1)
        
        # 6. Salvar resultados
        output_path = Path(args.output)
        print(f"💾 Salvando resultados em: {output_path.name}")
        df_output.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"   ✓ Arquivo salvo: {output_path.absolute()}")
        print()
        
        # 7. Exibir sumário
        print("=" * 70)
        print("📊 SUMÁRIO DAS PREDIÇÕES")
        print("=" * 70)
        print(f"Total de linhas processadas: {len(predictions)}")
        print(f"Confiança média: {predictions['CONFIANCA'].mean():.2%}")
        print(f"Confiança mínima: {predictions['CONFIANCA'].min():.2%}")
        print(f"Confiança máxima: {predictions['CONFIANCA'].max():.2%}")
        print()
        
        print("Distribuição de classes preditas:")
        class_counts = predictions['PEDRA_PREDITA'].value_counts()
        for pedra, count in class_counts.items():
            percentage = (count / len(predictions)) * 100
            print(f"  {pedra:12s}: {count:3d} ({percentage:5.1f}%)")
        print()
        
        print("🎯 Top 3 predições com maior confiança:")
        top_predictions = df_output.nlargest(3, 'CONFIANCA')[
            ['PEDRA_PREDITA', 'CONFIANCA'] + REQUIRED_FEATURES
        ]
        for idx, row in top_predictions.iterrows():
            print(f"  {idx+1}. {row['PEDRA_PREDITA']} ({row['CONFIANCA']:.2%} confiança)")
        print()
        
        print("=" * 70)
        print("✅ Processamento concluído com sucesso!")
        print("=" * 70)
        
    except FileNotFoundError as e:
        print(f"❌ Erro: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Erro de validação: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
