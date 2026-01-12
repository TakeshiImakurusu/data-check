"""
共通ユーティリティモジュール

各シリーズモジュール（dekispart, innosite, dekispart_school, cloud）で
共通して使用される関数を集約したモジュールです。
"""

import os
import configparser
from typing import Optional


def _normalize_odbc_driver(value: str) -> str:
    """
    ODBCドライバ名を正規化する。
    
    中括弧で囲まれている場合は除去して返す。
    
    Args:
        value: ODBCドライバ名
        
    Returns:
        正規化されたドライバ名
    """
    driver = value.strip()
    if driver.startswith('{') and driver.endswith('}'):
        driver = driver[1:-1]
    return driver


def _enable_deprecated_tls_if_requested(db_config: configparser.SectionProxy) -> None:
    """
    必要に応じて非推奨TLSを有効にする。
    
    config.iniでallow_deprecated_tlsがtrueに設定されている場合、
    環境変数ODBCIGNOREDEPRECATEDTLS=1を設定する。
    
    Args:
        db_config: configparserのセクションプロキシ
    """
    try:
        allow = db_config.getboolean('allow_deprecated_tls')
    except (ValueError, configparser.NoOptionError):
        allow = False
    if allow:
        os.environ['ODBCIGNOREDEPRECATEDTLS'] = '1'


def _build_sqlserver_conn_str(db_config: configparser.SectionProxy) -> str:
    """
    SQL Server用の接続文字列を構築する。
    
    Args:
        db_config: configparserのセクションプロキシ（DEKISPART_MNT_DB等）
        
    Returns:
        SQL Server接続文字列
    """
    _enable_deprecated_tls_if_requested(db_config)
    driver = _normalize_odbc_driver(db_config['driver'])
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={db_config['server']}",
        f"DATABASE={db_config['database']}",
        f"UID={db_config['uid']}",
        f"PWD={db_config['pwd']}"
    ]
    trust_flag = db_config.get('trust_server_certificate', '').strip()
    if trust_flag:
        parts.append(f"TrustServerCertificate={trust_flag}")
    encrypt_flag = db_config.get('encrypt', '').strip()
    if encrypt_flag:
        parts.append(f"Encrypt={encrypt_flag}")
    return ';'.join(parts) + ';'


class ConfigManager:
    """
    設定ファイルをキャッシュするシングルトンクラス。
    
    毎回ファイルを読み込む代わりに、初回に読み込んだ設定をキャッシュして返します。
    """
    _instance = None
    _config = None
    _config_file = 'config.ini'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_config(cls, config_file: str = 'config.ini', force_reload: bool = False) -> configparser.ConfigParser:
        """
        設定ファイルを読み込んでConfigParserオブジェクトを返す。
        
        キャッシュされている場合はキャッシュを返す。
        force_reload=Trueの場合は強制的に再読み込み。
        
        Args:
            config_file: 設定ファイルのパス（デフォルト: config.ini）
            force_reload: Trueの場合、キャッシュを無視して再読み込み
            
        Returns:
            ConfigParserオブジェクト
        """
        if cls._config is None or force_reload or cls._config_file != config_file:
            cls._config = configparser.ConfigParser()
            cls._config.read(config_file)
            cls._config_file = config_file
        return cls._config
    
    @classmethod
    def clear_cache(cls) -> None:
        """キャッシュをクリアする。テスト時などに使用。"""
        cls._config = None


def get_config(config_file: str = 'config.ini') -> configparser.ConfigParser:
    """
    設定ファイルを読み込んでConfigParserオブジェクトを返す。
    
    内部的にConfigManagerを使用してキャッシュを活用します。
    
    Args:
        config_file: 設定ファイルのパス（デフォルト: config.ini）
        
    Returns:
        ConfigParserオブジェクト
    """
    return ConfigManager.get_config(config_file)


def load_csv_with_encoding_detection(
    file_path: str,
    required_columns: Optional[list[str]] = None,
    encodings: Optional[list[str]] = None
) -> tuple[bool, any, str]:
    """
    複数のエンコーディングを試してCSVファイルを読み込む。
    
    Args:
        file_path: CSVファイルのパス
        required_columns: 必須カラムのリスト（Noneの場合はチェックしない）
        encodings: 試すエンコーディングのリスト
        
    Returns:
        (成功フラグ, DataFrame or None, エラーメッセージ)
    """
    import pandas as pd
    
    if not file_path or not os.path.exists(file_path):
        return False, None, f"ファイルが見つからないか、パスが無効です: {file_path}"
    
    if encodings is None:
        encodings = ['cp932', 'shift_jis', 'utf-8', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, engine='python', on_bad_lines='skip')
            if required_columns:
                missing = [col for col in required_columns if col not in df.columns]
                if missing:
                    return False, None, f"必要なカラム({', '.join(missing)})が不足しています。"
            return True, df, ""
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return False, None, f"ファイルの読み込み中にエラーが発生しました: {e}"
    
    return False, None, f"ファイル '{file_path}' を適切なエンコーディングで読み込めませんでした。"
