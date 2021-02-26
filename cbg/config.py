import configparser

_config = configparser.ConfigParser()


def read_config(file_name):
    """
    Reads the config properties from the given file.
    :param file_name: The path of the file to read from.
    """
    _config.read_file(open(file_name))


def get_config(section, key):
    """
    Gets a string value from the config.
    :param section: The section of the config.
    :param key: The key within the section to read.
    :return: The value of the config as a string.
    """
    return _config.get(section, key)


def get_float(section, key):
    """
    Gets a floating point value from the config.
    :param section: The section of the config.
    :param key: The key within the section to read.
    :return: The value of the config as a float.
    """
    return _config.getfloat(section, key)


def get_int(section, key):
    """
    Gets an Integer value from the config.
    :param section: The section of the config.
    :param key: The key within the section to read.
    :return: The value of the config as an Integer.
    """
    return _config.getint(section, key)


def get_bool(section, key):
    """
    Gets a boolean value from the config.
    :param section: The section of the config.
    :param key: The key within the section to read.
    :return: The value of the config as a bool.
    """
    return _config.getboolean(section, key)