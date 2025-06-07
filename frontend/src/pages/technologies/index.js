import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {
  
  const technologies = {
    backend: [
      {
        name: 'Python',
        description: 'Высокоуровневый язык программирования общего назначения с акцентом на читаемость кода',
        icon: 'https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white',
        version: '3.9+'
      },
      {
        name: 'Django',
        description: 'Высокоуровневый веб-фреймворк для Python, следующий принципу DRY (Don\'t Repeat Yourself)',
        icon: 'https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green',
        version: '3.2'
      },
      {
        name: 'Django REST Framework',
        description: 'Мощный и гибкий инструмент для создания веб-API на основе Django',
        icon: 'https://img.shields.io/badge/DRF-ff1709?style=for-the-badge&logo=django&logoColor=white',
        version: 'Latest'
      },
      {
        name: 'PostgreSQL',
        description: 'Объектно-реляционная система управления базами данных с открытым исходным кодом',
        icon: 'https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white',
        version: '13+'
      }
    ],
    frontend: [
      {
        name: 'React',
        description: 'JavaScript библиотека для создания пользовательских интерфейсов',
        icon: 'https://img.shields.io/badge/-ReactJs-61DAFB?style=for-the-badge&logo=react&logoColor=white',
        version: '17+'
      },
      {
        name: 'JavaScript',
        description: 'Высокоуровневый язык программирования для создания интерактивных веб-страниц',
        icon: 'https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black',
        version: 'ES6+'
      },
      {
        name: 'HTML5',
        description: 'Язык гипертекстовой разметки для создания структуры веб-страниц',
        icon: 'https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white',
        version: '5'
      },
      {
        name: 'CSS3',
        description: 'Каскадные таблицы стилей для описания внешнего вида документа',
        icon: 'https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white',
        version: '3'
      }
    ],
    devops: [
      {
        name: 'Docker',
        description: 'Платформа для разработки, доставки и запуска приложений в контейнерах',
        icon: 'https://img.shields.io/badge/docker-257bd6?style=for-the-badge&logo=docker&logoColor=white',
        version: 'Latest'
      },
      {
        name: 'Docker Compose',
        description: 'Инструмент для определения и запуска многоконтейнерных Docker приложений',
        icon: 'https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white',
        version: 'v2+'
      },
      {
        name: 'Nginx',
        description: 'Веб-сервер и обратный прокси-сервер для обслуживания статических файлов',
        icon: 'https://img.shields.io/badge/nginx-009639?style=for-the-badge&logo=nginx&logoColor=white',
        version: 'Latest'
      }
    ]
  }

  const TechnologyCard = ({ tech }) => (
    <div className={styles.techCard}>
      <div className={styles.techHeader}>
        <img src={tech.icon} alt={tech.name} className={styles.techIcon} />
        <div className={styles.techInfo}>
          <h3 className={styles.techName}>{tech.name}</h3>
          <span className={styles.techVersion}>v{tech.version}</span>
        </div>
      </div>
      <p className={styles.techDescription}>{tech.description}</p>
    </div>
  )

  return <Main>
    <MetaTags>
      <title>Технологии - Фудграм</title>
      <meta name="description" content="Фудграм - Технологии, используемые в проекте" />
      <meta property="og:title" content="Технологии - Фудграм" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Технологии</h1>
      <div className={styles.content}>
        <div>
          <div className={styles.section}>
            <h2 className={styles.subtitle}>Backend разработка</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Серверная часть приложения построена на современном стеке Python-технологий:
              </p>
              <div className={styles.techGrid}>
                {technologies.backend.map((tech, index) => (
                  <TechnologyCard key={index} tech={tech} />
                ))}
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.subtitle}>Frontend разработка</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Пользовательский интерфейс создан с использованием современных веб-технологий:
              </p>
              <div className={styles.techGrid}>
                {technologies.frontend.map((tech, index) => (
                  <TechnologyCard key={index} tech={tech} />
                ))}
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.subtitle}>DevOps и развертывание</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Для развертывания и управления приложением используются:
              </p>
              <div className={styles.techGrid}>
                {technologies.devops.map((tech, index) => (
                  <TechnologyCard key={index} tech={tech} />
                ))}
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <h2 className={styles.subtitle}>Архитектура проекта</h2>
            <div className={styles.text}>
              <ul className={styles.architectureList}>
                <li className={styles.textItem}>
                  <strong>SPA (Single Page Application)</strong> - одностраничное приложение на React
                </li>
                <li className={styles.textItem}>
                  <strong>REST API</strong> - RESTful веб-сервисы для взаимодействия frontend и backend
                </li>
                <li className={styles.textItem}>
                  <strong>Token Authentication</strong> - аутентификация на основе токенов
                </li>
                <li className={styles.textItem}>
                  <strong>Microservices Architecture</strong> - разделение на независимые сервисы
                </li>
                <li className={styles.textItem}>
                  <strong>Containerization</strong> - контейнеризация с помощью Docker
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
    </Container>
  </Main>
}

export default Technologies

