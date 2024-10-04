import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-about-enneatype',
  templateUrl: './about-enneatype.component.html',
  styleUrls: ['./about-enneatype.component.css']
})
export class AboutEnneatypeComponent implements OnInit {
  enneatypeNumber: number;
  enneatypeTitle: string = 'test';
  strengths: string[] = [];
  weaknesses: string[] = [];
  growth: string = '';
  stress: string = '';
  description: string = '';

  constructor() {
    const storedEnneatype = localStorage.getItem('enneatype');
    this.enneatypeNumber = storedEnneatype ? +storedEnneatype : 0;
  }

  ngOnInit() {
    this.loadEnneatypeInfo();
  }

  loadEnneatypeInfo() {
    switch (this.enneatypeNumber) {
      case 1:
        this.strengths = [
          'Strong sense of right and wrong, often striving to uphold high ethical standards.',
          'Dependable and responsible, making them reliable individuals in both personal and professional settings.',
          'High standards for self and others, which can lead to excellence but also to frustration when expectations are not met.',
          'Committed to improvement and growth, always seeking ways to enhance themselves and their environment.',
          'Practical and logical problem solvers who value efficiency and order in all aspects of life.'
        ];
        this.enneatypeTitle = 'The Reformer';
        this.weaknesses = [
          'Can be overly critical and judgmental, sometimes leading to conflict in relationships.',
          'Struggle with rigidity and perfectionism, which can hinder their ability to adapt to new situations.',
          'May repress anger or frustration, resulting in emotional build-up that can lead to outbursts.',
          'Tendency to be inflexible in views, making it difficult to see situations from different perspectives.',
          'Can become self-righteous or dogmatic, often believing their way is the only correct approach.'
        ];
        this.growth = 'Learn to embrace imperfection and accept that mistakes are part of life, allowing for greater personal and relational freedom.';
        this.stress = 'May become overly critical of themselves and others, leading to increased tension and conflict in their relationships.';
        this.description = 'Type 1s are principled, responsible, and perfectionistic individuals who strive for integrity and balance. They often feel a deep sense of duty to improve the world around them and can be seen as the moral compass in their communities.';
        break;
      case 2:
        this.enneatypeTitle = 'The Helper';
        this.strengths = [
          'Warm-hearted and generous, often going out of their way to help those in need.',
          'Empathetic and understanding, making them excellent listeners and supporters.',
          'Highly attuned to the needs of others, they can often sense when someone requires assistance.',
          'Motivated by love and connection, they thrive in relationships and social settings.',
          'Skilled at building relationships, they have a knack for bringing people together and fostering community.'
        ];
        this.weaknesses = [
          'Can be overly self-sacrificing, sometimes neglecting their own needs for the sake of others.',
          'Tendency to seek approval from others, which can lead to feelings of inadequacy.',
          'May become possessive or clingy in relationships, fearing abandonment.',
          'Struggle with boundary-setting, making it difficult to say no or prioritize themselves.',
          'Can neglect their own needs, resulting in burnout or resentment.'
        ];
        this.growth = 'Focus on self-care and setting healthy boundaries to maintain balance in their relationships and personal well-being.';
        this.stress = 'May experience anxiety if their efforts to please others are not reciprocated or appreciated, leading to feelings of being unvalued.';
        this.description = 'Type 2s are caring, interpersonal, and nurturing individuals who seek to be loved and needed. They often go out of their way to assist others, sometimes at the expense of their own needs and desires.';
        break;
      case 3:
        this.enneatypeTitle = 'The Achiever';
        this.strengths = [
          'Goal-oriented and driven, they are often successful in their pursuits.',
          'Adaptable and resourceful, able to navigate changing environments with ease.',
          'Highly motivated to achieve, they set ambitious goals and work diligently to reach them.',
          'Charismatic and charming, they are skilled at winning people over and making connections.',
          'Excellent at networking and public relations, often leveraging their social skills for professional advancement.'
        ];
        this.weaknesses = [
          'Can be overly focused on image and success, potentially sacrificing authenticity.',
          'Struggle with authenticity and vulnerability, often feeling pressure to maintain a façade.',
          'Tendency to compete excessively, which can lead to strained relationships.',
          'May neglect emotional connections in pursuit of goals, causing isolation.',
          'Can become workaholics, prioritizing career over personal life.'
        ];
        this.growth = 'Embrace authenticity over image, recognizing the value of emotional connections and the importance of being true to oneself.';
        this.stress = 'May become anxious or depressed if they feel they are not achieving their goals or are being compared to others, which can lead to feelings of inadequacy.';
        this.description = 'Type 3s are success-oriented, adaptable, and excelling individuals who often measure their self-worth by their achievements and the recognition they receive from others. They thrive in competitive environments and often take on leadership roles.';
        break;
      case 4:
        this.enneatypeTitle = 'The Individualist';
        this.strengths = [
          'Creative and artistic, often expressing themselves through various forms of art.',
          'Introspective and insightful, they have a deep understanding of their own emotions.',
          'Emotionally aware and sensitive, they can empathize with others on a profound level.',
          'Deeply connected to their feelings, they often experience a rich inner emotional life.',
          'Valuing individuality and uniqueness, they embrace what makes them different.'
        ];
        this.weaknesses = [
          'Can be moody and self-absorbed, leading to difficulties in relationships.',
          'Struggle with envy and comparison, often feeling that others have what they lack.',
          'Tendency to withdraw in times of distress, preferring solitude over social interactions.',
          'May dwell on past grievances, making it hard to move on from negative experiences.',
          'Can become overly dramatic, amplifying their emotions in ways that can overwhelm others.'
        ];
        this.growth = 'Learn to appreciate the present moment and find joy in simplicity, allowing for greater peace and satisfaction in life.';
        this.stress = 'May experience feelings of emptiness or isolation, leading to increased introspection and withdrawal from social situations.';
        this.description = 'Type 4s are individualistic, expressive, and emotionally deep individuals who seek to find their identity and significance in life. They often feel a longing for something missing and are driven by their unique perspectives and experiences.';
        break;
      case 5:
        this.enneatypeTitle = 'The Investigator';
        this.strengths = [
          'Analytical and perceptive, able to see details others might overlook.',
          'Independent and self-sufficient, they prefer to rely on themselves.',
          'Highly knowledgeable and skilled in their interests, they enjoy learning and understanding complex concepts.',
          'Curious and innovative, they often think outside the box and come up with original ideas.',
          'Strong problem-solving abilities, allowing them to tackle challenges effectively.'
        ];
        this.weaknesses = [
          'Can be overly detached or aloof, leading to difficulties in social interactions.',
          'Struggle with emotional expression, often keeping their feelings to themselves.',
          'Tendency to withdraw from social situations, preferring solitude over company.',
          'May hoard knowledge or resources, fearing that sharing will diminish their own value.',
          'Can become isolated in their thoughts, leading to a lack of engagement with the outside world.'
        ];
        this.growth = 'Engage more with the emotional side of life and foster connections with others to create a balanced existence.';
        this.stress = 'May feel overwhelmed by social demands or expectations, leading to increased withdrawal or anxiety about social situations.';
        this.description = 'Type 5s are intense observers and thinkers, often valuing knowledge and understanding above all else. They can be reserved and prefer solitude, focusing on their intellectual pursuits while occasionally struggling with emotional connection.';
        break;
      case 6:
        this.enneatypeTitle = 'The Loyalist';
        this.strengths = [
          'Loyal and committed, they value their relationships deeply and stand by their loved ones.',
          'Responsible and hardworking, they take their obligations seriously.',
          'Cautious and prepared, often thinking ahead to avoid potential problems.',
          'Highly reliable in relationships, they can be counted on in times of need.',
          'Valuing security and stability, they often create environments that feel safe and predictable.'
        ];
        this.weaknesses = [
          'Can be overly anxious or fearful, often worrying about potential threats.',
          'Struggle with indecisiveness, leading to difficulty in making choices.',
          'May become suspicious of others, causing rifts in relationships.',
          'Tendency to doubt their own abilities, resulting in a lack of confidence.',
          'Can become dependent on authority figures, looking to them for guidance and reassurance.'
        ];
        this.growth = 'Develop self-confidence and trust in their own instincts and decisions, allowing for greater independence and empowerment.';
        this.stress = 'May become overwhelmed with anxiety or paranoia when faced with uncertainty or danger, which can hinder their ability to act effectively.';
        this.description = 'Type 6s are reliable, trustworthy, and committed individuals who often seek security and support from their communities and relationships. They thrive in stable environments and often take on protective roles within their circles.';
        break;
        case 7:
          this.enneatypeTitle = 'The Enthusiast';
          this.strengths = [
            'Enthusiastic and energetic, they bring a sense of adventure and excitement to their endeavors.',
            'Highly optimistic, they tend to see the bright side of situations, inspiring others to adopt a positive outlook.',
            'Curious and open-minded, they embrace new experiences and ideas, constantly seeking to learn and grow.',
            'Creative and imaginative, they can think outside the box and generate innovative solutions to problems.',
            'Skilled at connecting with people, they often form a wide network of friends and acquaintances.'
          ];
          this.weaknesses = [
            'Can become easily distracted, struggling to focus on tasks and commitments over the long term.',
            'May avoid difficult emotions or situations, leading to a lack of depth in relationships.',
            'Tendency to overindulge in pleasure-seeking behaviors, which can result in impulsivity and recklessness.',
            'Struggles with commitment, often finding it difficult to stick to one path or decision.',
            'Might overlook important details, focusing more on the big picture or the next adventure.'
          ];
          this.growth = 'Learn to embrace stillness and introspection, allowing for deeper emotional connections and insights.';
          this.stress = 'In stressful situations, they may become scattered and anxious, leading to an overwhelming desire to escape or distract themselves.';
          this.description = 'Type 7s are enthusiastic, spontaneous, and versatile. They thrive on new experiences and adventures, often seeking to avoid pain or discomfort. Their zest for life makes them engaging companions, but their tendency to avoid difficult emotions can create challenges in their relationships.';
          break;
        case 8:
          this.enneatypeTitle = 'The Challenger';
          this.strengths = [
            'Confident and assertive, they possess strong leadership qualities and are not afraid to take charge.',
            'Protective and loyal, they stand up for their loved ones and advocate for their rights.',
            'Direct and honest, they communicate clearly and expect the same transparency from others.',
            'Highly energetic and determined, they pursue their goals with vigor and resilience.',
            'Possess a strong sense of justice, often fighting against unfairness and inequality.'
          ];
          this.weaknesses = [
            'Can be confrontational and aggressive, which may intimidate others and hinder collaboration.',
            'Tendency to be overly controlling, struggling to delegate tasks or trust others’ capabilities.',
            'May suppress vulnerability, finding it challenging to express emotions or show weakness.',
            'Struggles with impulsiveness, occasionally acting without considering the consequences of their actions.',
            'Can become overly focused on power or control, potentially alienating those around them.'
          ];
          this.growth = 'Embrace vulnerability and learn to express emotions more openly, fostering deeper connections with others.';
          this.stress = 'In times of stress, they may become domineering and defensive, feeling the need to control their environment to maintain a sense of security.';
          this.description = 'Type 8s are powerful, assertive, and self-confident individuals. They are natural leaders who value strength and independence. Their desire for control and justice often drives them to take bold actions, but their assertiveness can also lead to challenges in personal relationships.';
          break;
        case 9:
          this.enneatypeTitle = 'The Peacemaker';
          this.strengths = [
            'Calm and accepting, they create a soothing presence that helps others feel at ease.',
            'Good listeners and mediators, they possess a natural ability to foster harmony and cooperation among others.',
            'Patient and adaptable, they can go with the flow and accommodate various perspectives.',
            'Deeply empathetic, they have a genuine interest in understanding and valuing others’ feelings and viewpoints.',
            'Tend to avoid conflict, which can create a peaceful environment where everyone feels respected.'
          ];
          this.weaknesses = [
            'May struggle with inertia or complacency, finding it difficult to take action or make decisions.',
            'Can become overly accommodating, neglecting their own needs and desires in favor of maintaining peace.',
            'Tendency to disengage from issues, leading to avoidance of important conversations or conflicts.',
            'Might suppress emotions, resulting in unexpressed frustration or resentment over time.',
            'Can exhibit passive-aggressive behavior if feeling overwhelmed or pressured.'
          ];
          this.growth = 'Cultivate assertiveness and prioritize personal needs, recognizing that their voice and perspective are valuable.';
          this.stress = 'In stressful situations, they may withdraw and become complacent, avoiding necessary actions or decisions to cope with discomfort.';
          this.description = 'Type 9s are easygoing, accepting, and harmonious individuals who prioritize peace and stability. They often seek to avoid conflict and maintain a tranquil environment, but their tendency to neglect their own needs can lead to internal conflict and frustration over time.';
          break;
      }
    }
  }
  
