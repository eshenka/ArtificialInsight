import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { createPipeline, ScrapeRules } from '../api/api';

interface PipelineCreationPanelProps {
  onPipelineCreated: (token: string) => void;
}

interface FormData {
  user_name: string;
  description: string;
  language: string;
  entry_docs_url: string;
  max_depth: number;
  max_pages: number;
  scrape_patterns: {
    url_pattern: string;
    css_selector?: string;
  }[];
  forbidden_urls: {
    pattern: string;
  }[];
}

const PipelineCreationPanel: React.FC<PipelineCreationPanelProps> = ({ onPipelineCreated }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { register, handleSubmit, control, formState: { errors } } = useForm<FormData>({
    defaultValues: {
      user_name: '',
      description: '',
      language: 'en',
      entry_docs_url: '',
      max_depth: 3,
      max_pages: 50,
      scrape_patterns: [{ url_pattern: '', css_selector: '' }],
      forbidden_urls: []
    }
  });

  const { fields: patternFields, append: appendPattern, remove: removePattern } = 
    useFieldArray({ control, name: 'scrape_patterns' });
    
  const { fields: forbiddenFields, append: appendForbidden, remove: removeForbidden } = 
    useFieldArray({ control, name: 'forbidden_urls' });

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Transform the form data into the format expected by the API
      const rules: ScrapeRules = {
        max_depth: data.max_depth,
        max_pages: data.max_pages,
        scrape_patterns: data.scrape_patterns.map(pattern => ({
          url: { pattern: pattern.url_pattern },
          css_selector: pattern.css_selector || undefined
        })),
        forbidden_urls: data.forbidden_urls.map(url => ({ pattern: url.pattern }))
      };
      
      const response = await createPipeline(
        data.user_name,
        data.description,
        data.language,
        data.entry_docs_url,
        rules
      );
      
      onPipelineCreated(response.token);
    } catch (err: any) {
      setError(err?.message || 'Failed to create pipeline');
      console.error('Pipeline creation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-6 text-gray-800 dark:text-white">Create RAG Pipeline</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <div>
          <h3 className="text-md font-semibold mb-3 text-gray-700 dark:text-gray-300">Basic Information</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                User Name
              </label>
              <input
                type="text"
                {...register('user_name', { required: 'User name is required' })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              {errors.user_name && <p className="mt-1 text-sm text-red-600">{errors.user_name.message}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Description
              </label>
              <textarea
                {...register('description', { required: 'Description is required' })}
                rows={3}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              ></textarea>
              {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Language
              </label>
              <select
                {...register('language')}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="en">English</option>
                <option value="ru">Russian</option>
                {/* Add more languages as needed */}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Entry Documentation URL
              </label>
              <input
                type="url"
                {...register('entry_docs_url', { 
                  required: 'Entry URL is required',
                  pattern: {
                    value: /^(https?:\/\/)/,
                    message: 'Must be a valid URL starting with http:// or https://'
                  }
                })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              {errors.entry_docs_url && <p className="mt-1 text-sm text-red-600">{errors.entry_docs_url.message}</p>}
            </div>
          </div>
        </div>
        
        {/* Scraping Configuration */}
        <div>
          <h3 className="text-md font-semibold mb-3 text-gray-700 dark:text-gray-300">Scraping Configuration</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Maximum Depth
              </label>
              <input
                type="number"
                {...register('max_depth', { 
                  required: 'Max depth is required',
                  min: { value: 1, message: 'Min value is 1' },
                  max: { value: 10, message: 'Max value is 10' }
                })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                min="1"
                max="10"
              />
              {errors.max_depth && <p className="mt-1 text-sm text-red-600">{errors.max_depth.message}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Maximum Pages
              </label>
              <input
                type="number"
                {...register('max_pages', { 
                  required: 'Max pages is required',
                  min: { value: 1, message: 'Min value is 1' },
                  max: { value: 500, message: 'Max value is 500' }
                })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                min="1"
                max="500"
              />
              {errors.max_pages && <p className="mt-1 text-sm text-red-600">{errors.max_pages.message}</p>}
            </div>
          </div>
        </div>
        
        {/* Pattern Rules */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-md font-semibold text-gray-700 dark:text-gray-300">Pattern Rules</h3>
            <button
              type="button"
              onClick={() => appendPattern({ url_pattern: '', css_selector: '' })}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Add Rule
            </button>
          </div>
          
          <div className="space-y-4">
            {patternFields.map((field, index) => (
              <div key={field.id} className="p-4 border border-gray-200 rounded-md dark:border-gray-700">
                <div className="flex justify-between mb-2">
                  <h4 className="text-sm font-medium">Rule {index + 1}</h4>
                  <button
                    type="button"
                    onClick={() => removePattern(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Remove
                  </button>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      URL Pattern (regex)
                    </label>
                    <input
                      {...register(`scrape_patterns.${index}.url_pattern`, { 
                        required: 'URL pattern is required' 
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    {errors.scrape_patterns?.[index]?.url_pattern && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.scrape_patterns[index]?.url_pattern?.message}
                      </p>
                    )}
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      CSS Selector (optional)
                    </label>
                    <input
                      {...register(`scrape_patterns.${index}.css_selector`)}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Forbidden URLs */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-md font-semibold text-gray-700 dark:text-gray-300">Forbidden URLs</h3>
            <button
              type="button"
              onClick={() => appendForbidden({ pattern: '' })}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              Add URL Pattern
            </button>
          </div>
          
          <div className="space-y-2">
            {forbiddenFields.map((field, index) => (
              <div key={field.id} className="flex items-center space-x-2">
                <input
                  {...register(`forbidden_urls.${index}.pattern`, { 
                    required: 'Pattern is required' 
                  })}
                  placeholder="URL pattern to exclude (regex)"
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  type="button"
                  onClick={() => removeForbidden(index)}
                  className="p-2 rounded-md bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-800 dark:bg-red-900 dark:text-red-400"
                >
                  ✕
                </button>
              </div>
            ))}
            
            {forbiddenFields.length === 0 && (
              <p className="text-sm text-gray-500 italic">No forbidden URL patterns added yet.</p>
            )}
          </div>
        </div>
        
        {/* Submit Button */}
        <div className="pt-4">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full inline-flex justify-center py-3 px-6 border border-transparent shadow-sm text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating Pipeline...
              </span>
            ) : (
              'Create Pipeline'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PipelineCreationPanel;
