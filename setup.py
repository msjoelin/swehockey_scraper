from setuptools import setup, find_packages

with open('README.md') as readme_file:
    README = readme_file.read()

with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()

setup_args = dict(
    name='swehockey_scraper',
    version='1.4',
    description='Functions to scrape ice hockey data and statistics from swehockey',
    long_description_content_type="text/markdown",
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    packages=find_packages(),
    author='Marcus Sjölin',
    author_email='marcussjolin89@gmail.com',
    keywords=['ice hockey', 'scraping', 'sport analytics', 'shl', 'analys', 'ishockey', 'hockeyallsvenskan'],
    url='https://github.com/msjoelin/swehockey_scraper',
    download_url='https://pypi.org/project/swehockey_scraper/'
)

install_requires = [
    'numpy',
    'pandas',
    'bs4',
    'datetime', 
    'requests'
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)